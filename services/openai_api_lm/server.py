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

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
CONFIG_NAME = os.environ.get("CONFIG_NAME")
logger.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
NAMING = ["AI", "Human"]

with open(CONFIG_NAME, "r") as f:
    generation_params = json.load(f)
logger.info(f"Generation parameters: {generation_params}")

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")

def generate_responses(context, openai_api_key, openai_org, prompt, continue_last_uttr=False):
    outputs = []
    dialog_context = ""
    if prompt:
        dialog_context += prompt + "\n"
    s = len(context) % 2
    context = [f"{NAMING[(s + uttr_id) % 2]}: {uttr}" for uttr_id, uttr in enumerate(context)]
    if continue_last_uttr:
        dialog_context += "\n".join(context)
    else:
        dialog_context += "\n".join(context) + f"\n{NAMING[0]}:"

    logger.info(f"context inside generate_responses seen as: {dialog_context}")
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
    prompts = request.json.get("prompts", [])
    if len(contexts) > 0 and len(prompts) == 0:
        prompts = [""] * len(contexts)
    openai_api_keys = request.json.get("openai_api_keys", [])
    openai_orgs = request.json.get("openai_organizations", None)
    openai_orgs = [None] * len(contexts) if openai_orgs is None else openai_orgs

    try:
        responses = []
        for context, openai_api_key, openai_org, prompt in zip(contexts, openai_api_keys, openai_orgs, prompts):
            curr_responses = []
            outputs = generate_responses(context, openai_api_key, openai_org, prompt)
            for response in outputs:
                if len(response) >= 2:
                    curr_responses += [response]
                else:
                    curr_responses += [""]
            responses += [curr_responses]

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        responses = [[""]] * len(contexts)

    logger.info(f"openai-api-lm result: {responses}")
    total_time = time.time() - st_time
    logger.info(f"openai-api-lm exec time: {total_time:.3f}s")
    return jsonify(responses)
