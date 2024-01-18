import json
import logging
import os
import time
import sentry_sdk

from gigachat import GigaChat
from gigachat.models import Chat
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from common.prompts import META_GOALS_PROMPT_RU


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
logger.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
GIGACHAT_ROLES = ["assistant", "user"]

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")
DEFAULT_CONFIGS = {
    "GigaChat:1.3.23.1": json.load(open("common/generative_configs/gigachat.json", "r")),
}


def generate_responses(
    context,
    gigachat_api_key,
    gigachat_org,
    prompt,
    generation_params,
    continue_last_uttr=False,
):
    assert gigachat_api_key, logger.error("Error: GigaChat API key is not specified in env")
    giga = GigaChat(credentials=gigachat_api_key, verify_ssl_certs=False)

    s = len(context) % 2
    messages = [
        {"role": "system", "content": prompt},
    ]
    messages += [
        {
            "role": f"{GIGACHAT_ROLES[(s + uttr_id) % 2]}",
            "content": uttr,
        }
        for uttr_id, uttr in enumerate(context)
    ]
    logger.info(f"context inside generate_responses seen as: {messages}")

    payload = Chat(messages=messages, scope=gigachat_org, **generation_params)
    response = giga.chat(payload)

    outputs = [resp.message.content.strip() for resp in response.choices]

    return outputs


@app.route("/ping", methods=["POST"])
def ping():
    return "pong"


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("dialog_contexts", [])
    prompts = request.json.get("prompts", [])
    configs = request.json.get("configs", None)
    configs = [None] * len(prompts) if configs is None else configs
    configs = [DEFAULT_CONFIGS[PRETRAINED_MODEL_NAME_OR_PATH] if el is None else el for el in configs]

    if len(contexts) > 0 and len(prompts) == 0:
        prompts = [""] * len(contexts)

    gigachat_api_keys = request.json.get("gigachat_credentials", [])
    gigachat_orgs = request.json.get("gigachat_scopes", None)
    gigachat_orgs = [None] * len(contexts) if gigachat_orgs is None else gigachat_orgs

    try:
        responses = []
        for context, gigachat_api_key, gigachat_org, prompt, config in zip(
            contexts, gigachat_api_keys, gigachat_orgs, prompts, configs
        ):
            curr_responses = []
            outputs = generate_responses(context, gigachat_api_key, gigachat_org, prompt, config)
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

    logger.info(f"gigachat-api result: {responses}")
    total_time = time.time() - st_time
    logger.info(f"gigachat-api exec time: {total_time:.3f}s")
    return jsonify(responses)


@app.route("/generate_goals", methods=["POST"])
def generate_goals():
    st_time = time.time()

    prompts = request.json.get("prompts", None)
    prompts = [] if prompts is None else prompts
    configs = request.json.get("configs", None)
    configs = [None] * len(prompts) if configs is None else configs
    configs = [DEFAULT_CONFIGS[PRETRAINED_MODEL_NAME_OR_PATH] if el is None else el for el in configs]

    gigachat_api_keys = request.json.get("gigachat_credentials", [])
    gigachat_orgs = request.json.get("gigachat_scopes", None)
    gigachat_orgs = [None] * len(prompts) if gigachat_orgs is None else gigachat_orgs

    try:
        responses = []
        for gigachat_api_key, gigachat_org, prompt, config in zip(gigachat_api_keys, gigachat_orgs, prompts, configs):
            context = ["Привет", META_GOALS_PROMPT_RU + f"\nПромпт: '''{prompt}'''\nРезультат:"]
            goals_for_prompt = generate_responses(context, gigachat_api_key, gigachat_org, "", config)[0]
            logger.info(f"Generated goals: `{goals_for_prompt}` for prompt: `{prompt}`")
            responses += [goals_for_prompt]

    except Exception as exc:
        logger.info(exc)
        sentry_sdk.capture_exception(exc)
        responses = [""] * len(prompts)

    total_time = time.time() - st_time
    logger.info(f"gigachat-api generate_goals exec time: {total_time:.3f}s")
    return jsonify(responses)
