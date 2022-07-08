import logging
import time
import os

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import GPT2LMHeadModel, GPT2Tokenizer

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
logging.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
DEFAULT_CONFIDENCE = 0.9
N_HYPOTHESES_TO_GENERATE = int(os.environ.get("N_HYPOTHESES_TO_GENERATE", 1))
ZERO_CONFIDENCE = 0.0
MAX_HISTORY_DEPTH = 1

try:
    tokenizer = GPT2Tokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = GPT2LMHeadModel.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("dialogpt_multi is set to run on cuda")

    logger.info("dialogpt_multi is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def generate_response(context, model, tokenizer):
    encoded_context = []
    for uttr in context[-MAX_HISTORY_DEPTH:]:
        encoded_context += [tokenizer.encode(uttr + tokenizer.eos_token, return_tensors="pt")]
    bot_input_ids = torch.cat(encoded_context, dim=-1)

    with torch.no_grad():
        if torch.cuda.is_available():
            bot_input_ids = bot_input_ids.to("cuda")
        chat_history_ids = model.generate(
            bot_input_ids,
            min_length=100,
            max_length=100,
            eos_token_id=5,
            pad_token=1,
            do_sample=True,
            top_k=0,
            top_p=0.9,
            no_repeat_ngram_size=4)
        if torch.cuda.is_available():
            chat_history_ids = chat_history_ids.cpu()
    return tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1] :][0], skip_special_tokens=True)


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("utterances_histories", [])

    try:
        responses = []
        confidences = []
        for context in contexts:
            curr_responses = []
            curr_confidences = []
            for i in range(N_HYPOTHESES_TO_GENERATE):
                response = generate_response(context, model, tokenizer)
                if len(response) > 3:
                    # drop too short responses
                    curr_responses += [response]
                    curr_confidences += [DEFAULT_CONFIDENCE]
                else:
                    curr_responses += [""]
                    curr_confidences += [ZERO_CONFIDENCE]

            responses += [curr_responses]
            confidences += [curr_confidences]

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        responses = [[""]] * len(contexts)
        confidences = [[ZERO_CONFIDENCE]] * len(contexts)

    total_time = time.time() - st_time
    logger.info(f"dialogpt_multi exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))
