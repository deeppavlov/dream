import json
import logging
import os
import time

import anthropic
import sentry_sdk
from common.prompts import META_GOALS_PROMPT
from common.universal_templates import GENERATIVE_ROBOT_TEMPLATE
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
logger.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
NAMING = [anthropic.AI_PROMPT, anthropic.HUMAN_PROMPT]

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")
DEFAULT_CONFIGS = {
    "claude-1": json.load(open("common/generative_configs/anthropic_generative_config.json", "r")),
    "claude-instant-1": json.load(open("common/generative_configs/anthropic_generative_config.json", "r")),
}


def generate_responses(context, anthropic_api_key, prompt, generation_params, continue_last_uttr=False):
    assert anthropic_api_key, logger.error("Error: Anthropic API key is not specified in env")
    outputs = []

    dialog_context = f"{anthropic.HUMAN_PROMPT} "
    if prompt:
        dialog_context += prompt
    s = len(context) % 2
    context = [f"{NAMING[(s + uttr_id) % 2]} {uttr}" for uttr_id, uttr in enumerate(context)]
    if continue_last_uttr:
        dialog_context += "".join(context)
    else:
        dialog_context += "".join(context) + f"{NAMING[0]}"
    logger.info(f"context inside generate_responses seen as: {dialog_context}")

    client = anthropic.Client(api_key=anthropic_api_key)
    response = client.completion(
        prompt=dialog_context,
        stop_sequences=[NAMING[1]],
        model=PRETRAINED_MODEL_NAME_OR_PATH,
        **generation_params,
    )

    if isinstance(response, dict) and "completion" in response:
        outputs = [response["completion"].strip()]
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
    anthropic_api_keys = request.json.get("anthropic_api_keys", [])

    try:
        responses = []
        for context, anthropic_api_key, prompt, config in zip(contexts, anthropic_api_keys, prompts, configs):
            curr_responses = []
            outputs = generate_responses(context, anthropic_api_key, prompt, config)
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

    logger.info(f"anthropic-api result: {responses}")
    total_time = time.time() - st_time
    logger.info(f"anthropic-api exec time: {total_time:.3f}s")
    return jsonify(responses)


@app.route("/generate_goals", methods=["POST"])
def generate_goals():
    st_time = time.time()

    prompts = request.json.get("prompts", None)
    prompts = [] if prompts is None else prompts
    configs = request.json.get("configs", None)
    configs = [None] * len(prompts) if configs is None else configs
    configs = [DEFAULT_CONFIGS[PRETRAINED_MODEL_NAME_OR_PATH] if el is None else el for el in configs]
    anthropic_api_keys = request.json.get("anthropic_api_keys", [])
    try:
        responses = []
        for anthropic_api_key, prompt, config in zip(anthropic_api_keys, prompts, configs):
            context = ["hi", META_GOALS_PROMPT + f"\nPrompt: '''{prompt}'''\nResult:"]
            goals_for_prompt = generate_responses(context, anthropic_api_key, "", config)[0]
            logger.info(f"Generated goals: `{goals_for_prompt}` for prompt: `{prompt}`")
            responses += [goals_for_prompt]

    except Exception as exc:
        logger.info(exc)
        sentry_sdk.capture_exception(exc)
        responses = [""] * len(prompts)

    total_time = time.time() - st_time
    logger.info(f"anthropic-api generate_goals exec time: {total_time:.3f}s")
    return jsonify(responses)
