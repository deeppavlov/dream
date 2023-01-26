import logging
import json
import os
import time
import re

import sentry_sdk
import torch
from common.constants import CAN_CONTINUE_SCENARIO
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
MAX_HISTORY_DEPTH = os.environ.get("MAX_HISTORY_DEPTH")
MAX_HISTORY_DEPTH = int(MAX_HISTORY_DEPTH) if MAX_HISTORY_DEPTH else MAX_HISTORY_DEPTH
smiles_pattern = re.compile(r":[)(DpP3]")
with open(CONFIG_NAME, "r") as f:
    generation_params = json.load(f)
generation_params["num_return_sequences"] = N_HYPOTHESES_TO_GENERATE

try:
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = AutoModelForCausalLM.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("dialogpt is set to run on cuda")

    logger.info("dialogpt is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def generate_responses(context, model, tokenizer, continue_last_uttr=False):
    encoded_context = []

    if MAX_HISTORY_DEPTH:
        history_depth = MAX_HISTORY_DEPTH
        if len(context[-1].split()) > 3:
            history_depth = MAX_HISTORY_DEPTH - 1
        starting_index = -history_depth
    else:
        starting_index = 0

    for uttr in context[starting_index:-1]:
        encoded_context += [tokenizer.encode(uttr + " " + tokenizer.eos_token, return_tensors="pt")]
    if continue_last_uttr:
        encoded_context += [tokenizer.encode(context[-1] + " ", return_tensors="pt")]
    else:
        encoded_context += [tokenizer.encode(context[-1] + " " + tokenizer.eos_token, return_tensors="pt")]
    bot_input_ids = torch.cat(encoded_context, dim=-1)

    with torch.no_grad():
        if torch.cuda.is_available():
            bot_input_ids = bot_input_ids.to("cuda")
        chat_history_ids = model.generate(bot_input_ids, pad_token_id=tokenizer.eos_token_id, **generation_params)
        if torch.cuda.is_available():
            chat_history_ids = chat_history_ids.cpu()

    outputs = [tokenizer.decode(x[len(bot_input_ids[0]) :], skip_special_tokens=True) for x in chat_history_ids]
    return outputs


def cut_response(response):
    # if ends with a smile, it's finished
    if smiles_pattern.match(response[-2:]):
        return response

    leftover = re.split(r"[.!?]", response)[-1]
    if leftover:
        # strings with no ending punctuation will be empty
        response = response[: -len(leftover)]

    # save smiles from cutting
    smile = ""
    if smiles_pattern.match(leftover.strip()[:2]):
        smile = " " + leftover.strip()[:2]
    response += smile
    return response.strip()


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("utterances_histories", [])
    if len(contexts) == 0:
        contexts = request.json.get("dialog_contexts", [])

    try:
        responses = []
        confidences = []
        attributes = []
        for context in contexts:
            curr_responses = []
            curr_confidences = []
            curr_attributes = []
            outputs = generate_responses(context, model, tokenizer)
            for response in outputs:
                response = cut_response(response)
                if len(response) > 3:
                    # drop too short responses
                    curr_responses += [response]
                    curr_confidences += [DEFAULT_CONFIDENCE]
                    curr_attributes += [{"can_continue": CAN_CONTINUE_SCENARIO}]
                else:
                    curr_responses += [""]
                    curr_confidences += [ZERO_CONFIDENCE]
                    curr_attributes += [{}]

            responses += [curr_responses]
            confidences += [curr_confidences]
            attributes += [curr_attributes]

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        responses = [[""]] * len(contexts)
        confidences = [[ZERO_CONFIDENCE]] * len(contexts)
        attributes = [[{}]] * len(contexts)

    total_time = time.time() - st_time
    logger.info(f"dialogpt exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences, attributes)))


@app.route("/continue", methods=["POST"])
def continue_last_uttr():
    st_time = time.time()
    contexts = request.json.get("utterances_histories", [])
    if len(contexts) == 0:
        contexts = request.json.get("dialog_contexts", [])

    try:
        responses = []
        for context in contexts:
            curr_responses = []
            outputs = generate_responses(context, model, tokenizer, continue_last_uttr=True)
            for response in outputs:
                response = cut_response(response)
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
    logger.info(f"dialogpt continue exec time: {total_time:.3f}s")
    return jsonify(responses)
