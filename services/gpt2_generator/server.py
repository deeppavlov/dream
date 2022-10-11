import logging
import time
import os
import re
import json
import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from itertools import cycle

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
CONFIG_NAME = os.environ.get("CONFIG_NAME")
N_HYPOTHESES_TO_GENERATE = int(os.environ.get("N_HYPOTHESES_TO_GENERATE"))
MAX_HISTORY_DEPTH = int(os.environ.get("MAX_HISTORY_DEPTH"))
logging.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")

DEFAULT_CONFIDENCE = 0.9
ZERO_CONFIDENCE = 0.0

with open(CONFIG_NAME, "r") as f:
    generation_params = json.load(f)
generation_params["num_return_sequences"] = N_HYPOTHESES_TO_GENERATE

NICK_COMPILED = re.compile(r"\@[^\s]+\b")
SPECIFIC_SYMBOLS = r"[#$%&()*+/;<=>@\^_`{|}~\[\]�]"
SPECIFIC_WORDS_COMPILED = re.compile(rf"{SPECIFIC_SYMBOLS}[a-zA-Z]+{SPECIFIC_SYMBOLS}")
URLS_COMPILED = re.compile(r"(http[^\s]+\b|<a href[^>]+>)")
ANYTHING_EXCEPT_OF_LETTERS_SPACE_AND_PUNCT_COMPILED = re.compile(SPECIFIC_SYMBOLS)
NEW_UTTERANCE = ""

try:
    tokenizer = GPT2Tokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = GPT2LMHeadModel.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("gpt2-generator is set to run on cuda")

    logger.info("gpt2-generator is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def generate_response(context, model, tokenizer):
    text = "\n".join(
        list(map(lambda x: NEW_UTTERANCE.join(x), zip(cycle(["", ""]), context[-MAX_HISTORY_DEPTH:] + [""])))
    )
    bot_input_ids = tokenizer.encode(text, return_tensors="pt")
    with torch.no_grad():
        if torch.cuda.is_available():
            bot_input_ids = bot_input_ids.to("cuda")

        chat_history_ids = model.generate(bot_input_ids, pad_token_id=tokenizer.eos_token_id, **generation_params)
        if torch.cuda.is_available():
            chat_history_ids = chat_history_ids.cpu()

    outputs = [
        tokenizer.decode(x, skip_special_tokens=True)[len(text) :].lstrip().split("\n")[0] for x in chat_history_ids
    ]
    outputs = [re.sub(NICK_COMPILED, "", response) for response in outputs]
    outputs = [re.sub(URLS_COMPILED, "", response) for response in outputs]
    outputs = [re.sub(SPECIFIC_WORDS_COMPILED, "", response) for response in outputs]
    outputs = [ANYTHING_EXCEPT_OF_LETTERS_SPACE_AND_PUNCT_COMPILED.sub("", response).strip() for response in outputs]
    return outputs


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
            preds = generate_response(context, model, tokenizer)
            for response in preds:
                response = re.sub(NICK_COMPILED, "", response).strip()

                if len(response) > 3:
                    # drop too short responses
                    curr_responses += [response]
                    curr_confidences += [DEFAULT_CONFIDENCE]
                else:
                    curr_responses += [""]
                    curr_confidences += [ZERO_CONFIDENCE]
            logger.info(f"gpt2-generator for context: `{context}`\n returns: {curr_responses}")
            responses += [curr_responses]
            confidences += [curr_confidences]

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        responses = [[""]] * len(contexts)
        confidences = [[ZERO_CONFIDENCE]] * len(contexts)

    total_time = time.time() - st_time
    logger.info(f"gpt2-generator exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))
