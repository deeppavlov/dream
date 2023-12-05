import json
import logging
import os
import time
import sentry_sdk

from openai import OpenAI
from common.prompts import META_GOALS_PROMPT
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
DEFAULT_CONFIGS = {
    "text-davinci-003": json.load(open("common/generative_configs/openai-text-davinci-003.json", "r")),
    "gpt-3.5-turbo": json.load(open("common/generative_configs/openai-chatgpt.json", "r")),
    "gpt-3.5-turbo-16k": json.load(open("common/generative_configs/openai-chatgpt.json", "r")),
    "gpt-4": json.load(open("common/generative_configs/openai-chatgpt.json", "r")),
    "gpt-4-32k": json.load(open("common/generative_configs/openai-chatgpt.json", "r")),
    "gpt-4-1106-preview": json.load(open("common/generative_configs/openai-chatgpt.json", "r")),
}
CHAT_COMPLETION_MODELS = ["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-32k", "gpt-4-1106-preview"]


def generate_responses(context, openai_api_key, openai_org, prompt, generation_params, continue_last_uttr=False):
    outputs = []

    assert openai_api_key, logger.error("Error: OpenAI API key is not specified in env")
    client = OpenAI(api_key=openai_api_key, organization=openai_org if openai_org else None)

    if PRETRAINED_MODEL_NAME_OR_PATH in CHAT_COMPLETION_MODELS:
        logger.info("Use special chat completion endpoint")
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
        response = client.chat.completions.create(
            model=PRETRAINED_MODEL_NAME_OR_PATH, messages=messages, **generation_params
        )
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
        response = client.completions.create(
            model=PRETRAINED_MODEL_NAME_OR_PATH, prompt=dialog_context, **generation_params
        )

    response = response.model_dump()
    outputs = [
        resp["message"]["content"].strip() if "message" in resp else resp.get("text", "").strip()
        for resp in response["choices"]
    ]

    if PRETRAINED_MODEL_NAME_OR_PATH not in CHAT_COMPLETION_MODELS:
        # post-processing of the responses by all models except of ChatGPT
        outputs = [GENERATIVE_ROBOT_TEMPLATE.sub("\n", resp).strip() for resp in outputs]
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
    openai_api_keys = request.json.get("openai_api_keys", [])
    openai_orgs = request.json.get("openai_api_organizations", None)
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


@app.route("/generate_goals", methods=["POST"])
def generate_goals():
    st_time = time.time()

    prompts = request.json.get("prompts", None)
    prompts = [] if prompts is None else prompts
    configs = request.json.get("configs", None)
    configs = [None] * len(prompts) if configs is None else configs
    configs = [DEFAULT_CONFIGS[PRETRAINED_MODEL_NAME_OR_PATH] if el is None else el for el in configs]
    openai_api_keys = request.json.get("openai_api_keys", [])
    openai_orgs = request.json.get("openai_api_organizations", None)
    openai_orgs = [None] * len(prompts) if openai_orgs is None else openai_orgs
    try:
        responses = []
        for openai_api_key, openai_org, prompt, config in zip(openai_api_keys, openai_orgs, prompts, configs):
            context = ["hi", META_GOALS_PROMPT + f"\nPrompt: '''{prompt}'''\nResult:"]
            goals_for_prompt = generate_responses(context, openai_api_key, openai_org, "", config)[0]
            logger.info(f"Generated goals: `{goals_for_prompt}` for prompt: `{prompt}`")
            responses += [goals_for_prompt]

    except Exception as exc:
        logger.info(exc)
        sentry_sdk.capture_exception(exc)
        responses = [""] * len(prompts)

    total_time = time.time() - st_time
    logger.info(f"openai-api generate_goals exec time: {total_time:.3f}s")
    return jsonify(responses)
