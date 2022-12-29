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


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
CONFIG_NAME = os.environ.get("CONFIG_NAME")
logging.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
DEFAULT_CONFIDENCE = 0.9
ZERO_CONFIDENCE = 0.0
MAX_HISTORY_DEPTH = 3
with open(CONFIG_NAME, "r") as f:
    generation_params = json.load(f)
max_length = generation_params["max_length"]
del generation_params["max_length"]

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def generate_responses(
    instruction, context, model, tokenizer, continue_last_uttr=False
):
    outputs = []
    dialog_context = instruction + "\n" + "\n".join(context) + "\n" + "AI:"
    logger.info(f"context_1 inside generate_responses seen as: {[dialog_context]}")
    bot_input_ids = tokenizer([dialog_context], return_tensors="pt").input_ids
    with torch.no_grad():
        if torch.cuda.is_available():
            bot_input_ids = bot_input_ids.to("cuda")
        chat_history_ids = model.generate(
            bot_input_ids,
            max_length=len(tokenizer(dialog_context)["input_ids"]) + max_length,
            pad_token_id=tokenizer.eos_token_id,
            **generation_params,
        )
        # сделать чтоб параметры брались из файлы !!!
    if torch.cuda.is_available():
        chat_history_ids = chat_history_ids.cpu()
    for result in chat_history_ids:
        output = tokenizer.decode(result, skip_special_tokens=True)
        logger.info(f"full output: {[output]}")
        logger.info(f"full dialog_context: {[dialog_context]}")
        split_output = output.replace(dialog_context + " ", "")
        logger.info(f"split output: {split_output}")
        split_output_1 = output.replace(dialog_context, "").split("\n")
        logger.info(f"split output_1: {split_output_1}")
        result_cut = output.replace(dialog_context + " ", "").split("\n")[0]
        outputs.append(result_cut)
    return outputs


try:
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = AutoModelForCausalLM.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("gptj is set to run on cuda")
    example_response = generate_responses(
        "", "Hello! Let's chat!", model, tokenizer, continue_last_uttr=False
    )
    logger.info(f"example response: {example_response}")
    logger.info("gptj is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("dialog_context", [])
    try:
        responses = []
        confidences = []
        for context in contexts:
            outputs = generate_responses("", context, model, tokenizer)
            logger.info(f"outputs: {outputs}")
            for response in outputs:
                if len(response) > 3:
                    # drop too short responses
                    responses += [response]
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
    logger.info(f"gptj exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))
