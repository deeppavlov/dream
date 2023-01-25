import logging
import json
import os
import time

import openai
import sentry_sdk
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
CONFIG_NAME = os.environ.get("CONFIG_NAME")
logging.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
DEFAULT_CONFIDENCE = 0.9
ZERO_CONFIDENCE = 0.0
MAX_HISTORY_DEPTH = 3
with open(CONFIG_NAME, "r") as f:
    generation_params = json.load(f)
logging.info(f"Generation parameters: {generation_params}")

OPENAI_KEY = os.environ.get("OPENAI_KEY", "")
OPENAI_ORGANIZATION = os.environ.get("OPENAI_ORGANIZATION", "")
assert OPENAI_ORGANIZATION, logger.error(f"Error: OpenAI organization is not specified in env")
assert OPENAI_KEY, logger.error(f"Error: OpenAI key is not specified in env")
openai.organization = OPENAI_ORGANIZATION
openai.api_key = OPENAI_KEY


def generate_responses(instruction, context, continue_last_uttr=False):
    outputs = []
    if continue_last_uttr:
        dialog_context = instruction + "\n" + "\n".join(context)
    else:
        dialog_context = instruction + "\n" + "\n".join(context) + "\n" + "AI:"
    logger.info(f"context inside generate_responses seen as: {[dialog_context]}")

    response = openai.Completion.create(
        model=PRETRAINED_MODEL_NAME_OR_PATH,
        prompt=context,
        **generation_params
    )

    if isinstance(response, dict) and "choices" in response:
        outputs = [resp.get("text", "") for resp in response["choices"]]
    elif isinstance(response, str):
        outputs = [response]

    return outputs


try:
    example_response = generate_responses(
        "",
        ["Question: What is the goal of SpaceX? Answer: To revolutionize space transportation. "],
        continue_last_uttr=False,
    )
    logger.info(f"example response: {example_response}")
    logger.info("openai-api-lm is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("dialog_contexts", [])
    try:
        responses = []
        confidences = []
        for context in contexts:
            outputs = generate_responses("", context)
            logger.info(f"outputs: {outputs}")
            for response in outputs:
                if len(response) >= 3:
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
    logger.info(f"transformers_lm exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))
