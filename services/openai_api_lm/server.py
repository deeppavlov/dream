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
with open(CONFIG_NAME, "r") as f:
    generation_params = json.load(f)
logging.info(f"Generation parameters: {generation_params}")


def generate_responses(instruction, context, openai_api_key, openai_org, continue_last_uttr=False):
    outputs = []
    if continue_last_uttr:
        dialog_context = instruction + "\n" + "\n".join(context)
    else:
        dialog_context = instruction + "\n" + "\n".join(context) + "\n" + "AI:"
    logger.info(f"context inside generate_responses seen as: {[dialog_context]}")

    assert openai_api_key, logger.error(f"Error: OpenAI API key is not specified in env")
    openai.api_key = openai_api_key
    openai.organization = openai_org if openai_org else None

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


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("dialog_contexts", [])
    openai_api_keys = request.json.get("openai_api_keys", [])
    openai_organizations = request.json.get("openai_organizations", None)
    openai_organizations = [None] * len(contexts) if openai_organizations is None else openai_organizations

    try:
        responses = []
        confidences = []
        for context, openai_api_key, openai_org in zip(contexts, openai_api_keys, openai_organizations):
            outputs = generate_responses("", context, openai_api_key, openai_org)
            logger.info(f"openai-api-lm result: {outputs}")
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
    logger.info(f"openai-api-lm exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))
