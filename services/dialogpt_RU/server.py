import logging
import time
import os

from transformers import BertTokenizer, BertForMaskedLM
import torch
from flask import Flask, request, jsonify
from healthcheck import HealthCheck
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
logging.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
MASK_ID = 103
try:
    cuda = torch.cuda.is_available()
    if cuda:
        torch.cuda.set_device(0)  # singe gpu
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    logger.info(f"masked_lm is set to run on {device}")

    # init model
    tokenizer = BertTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = BertForMaskedLM.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model.eval()
    if cuda:
        model.cuda()

    logger.info("masked_lm model is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")
logging.getLogger("werkzeug").setLevel("WARNING")


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    text = request.json.get("text", [])
    try:
        inputs = tokenizer(text, return_tensors="pt", padding=True)
        inputs = {k: v.cuda() for k, v in inputs.items()} if cuda else inputs
        logits = model(**inputs).logits.cpu()
        probs = torch.nn.functional.softmax(logits, dim=2)

        batch_predicted_tokens = []
        for batch_i in range(probs.shape[0]):
            masked_tokens = probs[batch_i][inputs["input_ids"][batch_i] == MASK_ID]
            predicted_tokens = []
            for token_id in range(masked_tokens.shape[0]):
                token_probs, token_ids = masked_tokens[token_id].topk(10)
                token_probs = token_probs.tolist()
                token_ids = [tokenizer.decode([id]) for id in token_ids.tolist()]
                predicted_tokens.append({token: prob for token, prob in zip(token_ids, token_probs)})
            batch_predicted_tokens.append(predicted_tokens)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        batch_predicted_tokens = [[]] * len(text)

    total_time = time.time() - st_time
    logger.info(f"masked_lm exec time: {total_time:.3f}s")
    return jsonify({"predicted_tokens": batch_predicted_tokens})
