import logging
import json
import os
import time
import sys

import sentry_sdk

import openai

from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])



logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
CONFIG_NAME = os.environ.get("CONFIG_NAME")

if CONFIG_NAME is None:
    CONFIG_NAME = "config_local.json"

logging.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
DEFAULT_CONFIDENCE = 0.9
ZERO_CONFIDENCE = 0.0
MAX_HISTORY_DEPTH = 3

open_ai_org = ""
open_ai_key = ""

with open(CONFIG_NAME, "r") as f:
    generation_params = json.load(f)
# max_length = generation_params.get("max_length", 50)
open_ai_key = generation_params.get("open_ai_key", "")
open_ai_org = generation_params.get("open_ai_org", "")
# del generation_params["max_length"]

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")

openai.organization = open_ai_org
openai.api_key = open_ai_key


def generate_responses(
    instruction, context, continue_last_uttr=False
):
    outputs = []
    dialog_context = instruction + "\n" + "\n".join(context) + "\n" + "AI:"
    logger.info(f"context inside generate_responses seen as: {[dialog_context]}")
    
    result = ""

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=context,
        max_tokens=64,
        temperature=0.4,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    if "choices" in response:
        if len(response["choices"]):
            if "text" in response["choices"][0]:
                result = response["choices"][0]["text"]
   

    # logger.info(f"full output: {[output]}")
    # result_cut = output.replace(dialog_context + " ", "").split("\n")[0]
    # outputs.append(result_cut)
    outputs.append(result)
    return outputs


try:
    # return the full result
    example_response = generate_responses(
        "",
        "Question: What is the goal of SpaceX? Answer: ",
        continue_last_uttr=False,
    )
    logger.info(f"example response: {example_response}")
    logger.info("GPT-3.5 is ready")
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
            outputs = generate_responses("", context)
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
    logger.info(f"GPT-3.5 exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))
