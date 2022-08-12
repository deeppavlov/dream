import logging
import os
import time

from flask import Flask, request, jsonify
import sentry_sdk
import torch
from torch.nn import functional as F
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import AutoTokenizer, AutoModel


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
logging.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


try:
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = AutoModel.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)

    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("sentence_ranker is set to run on cuda")

    logger.info("sentence_ranker is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


def transform(data):
    utterances = []
    for past_uttr, past_response in zip(data["pastUtterances"], data["pastResponses"]):
        utterances.append(past_uttr)
        utterances.append(past_response)
    utterances.append(data["currentUtterance"])
    return " ".join(utterances)


@app.route("/batch_model", methods=["POST"])
def batch_respond():
    t = time.time()
    data = request.json
    sentence = transform(request.json)
    inputs = tokenizer.batch_encode_plus([sentence] + data["hypotheses"], return_tensors="pt", padding=True)

    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    if torch.cuda.is_available():
        input_ids = input_ids.cuda()
        attention_mask = attention_mask.cuda()

    output = model(input_ids, attention_mask=attention_mask)[0]
    sentence_rep = output[:1].mean(dim=1)
    label_reps = output[1:].mean(dim=1)

    result = F.cosine_similarity(sentence_rep, label_reps)

    if torch.cuda.is_available():
        result = result.cpu()

    result = result.detach().numpy()
    result = [i for i in result]

    logger.info(f"sentense_ranker exec time {round(time.time()-t, 2)} sec")
    return jsonify([{"batch": [float(str(i)) for i in result]}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
