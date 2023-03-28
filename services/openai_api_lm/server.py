import logging
import os
import time

import openai
import sentry_sdk
from common.universal_templates import GENERATIVE_ROBOT_TEMPLATE
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
logger.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
NAMING = ["AI", "Human"]
CHATGPT_ROLES = ["assistant", "user"]

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def generate_responses(context, openai_api_key, openai_org, prompt, generation_params, continue_last_uttr=False):
    outputs = []

    assert openai_api_key, logger.error("Error: OpenAI API key is not specified in env")
    openai.api_key = openai_api_key
    openai.organization = openai_org if openai_org else None

    if PRETRAINED_MODEL_NAME_OR_PATH == "gpt-3.5-turbo":
        logger.info("model=gpt-3.5-turbo, use special chat completion endpoint")
        s = len(context) % 2
        messages = [
            {"role": "system", "content": prompt},
        ]
        messages += [
            {
                "role": f"{CHATGPT_ROLES[(s + uttr_id) % 2]}",
                "content": uttr,
            }
            for uttr_id, uttr in enumerate(context)
        ]
        logger.info(f"context inside generate_responses seen as: {messages}")
        response = openai.ChatCompletion.create(model=PRETRAINED_MODEL_NAME_OR_PATH, messages=messages)
    else:
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
        response = openai.Completion.create(
            model=PRETRAINED_MODEL_NAME_OR_PATH,
            prompt=dialog_context,
            **generation_params,
        )

    if isinstance(response, dict) and "choices" in response:
        outputs = [
            resp["message"]["content"].strip() if "message" in resp else resp.get("text", "").strip()
            for resp in response["choices"]
        ]
    elif isinstance(response, str):
        outputs = [response.strip()]

    outputs = [GENERATIVE_ROBOT_TEMPLATE.sub("\n", resp).strip() for resp in outputs]
    outputs = [resp.split("\n")[0] for resp in outputs]
    return outputs


@app.route("/ping", methods=["POST"])
def ping():
    return "pong"


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("dialog_contexts", [])
    prompts = request.json.get("prompts", [])
    configs = request.json.get("configs", [])
    if len(contexts) > 0 and len(prompts) == 0:
        prompts = [""] * len(contexts)
    openai_api_keys = request.json.get("OPENAI_API_KEY_list", [])
    openai_orgs = request.json.get("OPENAI_ORGANIZATION_list", None)
    openai_orgs = [None] * len(contexts) if openai_orgs is None else openai_orgs

    try:
        responses = []
        for context, openai_api_key, openai_org, prompt, config in zip(
            contexts, openai_api_keys, openai_orgs, prompts, configs
        ):
            curr_responses = []
            outputs = generate_responses(context, openai_api_key, openai_org, prompt, config)
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

    logger.info(f"openai-api result: {responses}")
    total_time = time.time() - st_time
    logger.info(f"openai-api exec time: {total_time:.3f}s")
    return jsonify(responses)
