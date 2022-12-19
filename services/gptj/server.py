import logging
import json
import os
import time

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import AutoModelForCausalLM, AutoTokenizer

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
N_HYPOTHESES_TO_GENERATE = int(os.environ.get("N_HYPOTHESES_TO_GENERATE", 1))
CONFIG_NAME = os.environ.get("CONFIG_NAME")
logging.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
DEFAULT_CONFIDENCE = 0.9
ZERO_CONFIDENCE = 0.0
MAX_HISTORY_DEPTH = 3
with open(CONFIG_NAME, "r") as f:
    generation_params = json.load(f)
generation_params["num_return_sequences"] = N_HYPOTHESES_TO_GENERATE
generation_params["num_return_sequences"] = 3

try:
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = AutoModelForCausalLM.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("gptj is set to run on cuda")
        logger.info(f"{PRETRAINED_MODEL_NAME_OR_PATH} is model name")

    logger.info("gptj is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def generate_responses(context, model, tokenizer, continue_last_uttr=False):
    # encoded_context = []
    # for uttr in context[-MAX_HISTORY_DEPTH:-1]:
    #     encoded_context += [tokenizer.encode(uttr + " " + tokenizer.eos_token, return_tensors="pt")]
    # if continue_last_uttr:
    #     encoded_context += [tokenizer.encode(context[-1] + " ", return_tensors="pt")]
    # else:
    #     encoded_context += [tokenizer.encode(context[-1] + " " + tokenizer.eos_token, return_tensors="pt")]
    # bot_input_ids = torch.cat(encoded_context, dim=-1)
    logger.info(f"context_1 inside generate_responses seen as: {context}")
    bot_input_ids = tokenizer(context, return_tensors="pt").input_ids
    with torch.no_grad():
        if torch.cuda.is_available():
            bot_input_ids = bot_input_ids.to("cuda")
        #generation_params["max_length"] = len(bot_input_ids) + generation_params["max_length"]
        chat_history_ids = model.generate(bot_input_ids, max_length=len(tokenizer(context)['input_ids'])+40, min_length=8, top_p=0.9, temperature=0.9, do_sample=True, pad_token_id=tokenizer.eos_token_id)
    if torch.cuda.is_available():
        chat_history_ids = chat_history_ids.cpu()

    output = tokenizer.decode(chat_history_ids[0], skip_special_tokens=True)
    return output


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("utterances_histories", [])
    logger.info(f"contexts seen as: {contexts}")
    try:
        responses = []
        confidences = []
        for context in contexts:
            curr_responses = []
            curr_confidences = []
            logger.info(f"context_1 seen as: {context}")
            outputs = generate_responses(context, model, tokenizer)
            # for response in outputs:
            #     if len(response) > 3:
            #         # drop too short responses
            #         curr_responses += [response]
            #         curr_confidences += [DEFAULT_CONFIDENCE]
            #     else:
            #         curr_responses += [""]
            #         curr_confidences += [ZERO_CONFIDENCE]
            if len(outputs) > 3:
                # drop too short responses
                responses += [outputs]
                confidences += [DEFAULT_CONFIDENCE]
            else:
                responses += [""]
                confidences += [ZERO_CONFIDENCE]

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        responses = [[""]] * len(contexts)
        confidences = [[ZERO_CONFIDENCE]] * len(contexts)

    total_time = time.time() - st_time
    logger.info(f"dialogpt exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))


@app.route("/continue", methods=["POST"])
def continue_last_uttr():
    st_time = time.time()
    contexts = request.json.get("utterances_histories", [])

    try:
        responses = []
        for context in contexts:
            curr_responses = []
            outputs = generate_responses(context, model, tokenizer, continue_last_uttr=True)
            for response in outputs:
                if len(response) > 3:
                    # drop too short responses
                    curr_responses += [response]
                else:
                    curr_responses += [""]

            responses += [curr_responses]

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        responses = [[""]] * len(contexts)

    total_time = time.time() - st_time
    logger.info(f"gptj continue exec time: {total_time:.3f}s")
    return jsonify(responses)
