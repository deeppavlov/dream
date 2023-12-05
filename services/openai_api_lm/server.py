import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import openai
import sentry_sdk
import tiktoken
from common.prompts import META_GOALS_PROMPT
from common.text_processing_for_prompts import check_token_number
from common.universal_templates import GENERATIVE_ROBOT_TEMPLATE
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def dump_stats(requests_stats, statistics_fpath, create_file=False):
    mode = "w" if create_file else "a"
    with open(statistics_fpath, mode) as f:
        for line in requests_stats:
            f.write(json.dumps(line) + "\n")
    return datetime.now()


PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
logger.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")

STATISTICS_FILES_PATH = os.environ.get("STATISTICS_FILES_PATH", "stats/")

now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
model_name = PRETRAINED_MODEL_NAME_OR_PATH.replace(".", "")
folder = Path("/data/").joinpath(STATISTICS_FILES_PATH)
folder.mkdir(parents=True, exist_ok=True)
statistics_fpath = folder.joinpath(f"stats_{model_name}_{now}.txt")
prev_dump_datetime = dump_stats([{}], statistics_fpath, create_file=True)
requests_stats = []

NAMING = ["AI", "Human"]
CHATGPT_ROLES = ["assistant", "user"]

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")
DEFAULT_CONFIGS = {
    "text-davinci-003": json.load(open("common/generative_configs/openai-text-davinci-003.json", "r")),
    "davinci-002": json.load(open("common/generative_configs/davinci-002.json", "r")),
    "gpt-3.5-turbo": json.load(open("common/generative_configs/openai-chatgpt.json", "r")),
    "gpt-3.5-turbo-16k": json.load(open("common/generative_configs/openai-chatgpt.json", "r")),
    "gpt-4": json.load(open("common/generative_configs/openai-chatgpt.json", "r")),
    "gpt-4-32k": json.load(open("common/generative_configs/openai-chatgpt.json", "r")),
    # that is gpt-4-turbo
    "gpt-4-1106-preview": json.load(open("common/generative_configs/openai-chatgpt-long.json", "r")),
}
CHAT_COMPLETION_MODELS = ["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-32k", "gpt-4-1106-preview"]
MAX_TOKENS = {
    "text-davinci-003": 4097,
    "davinci-002": 4097,
    "gpt-3.5-turbo": 4096,
    "gpt-3.5-turbo-16k": 16384,
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    # gpt4-turbo set to 64k instead of 128k on purpose
    # as it was shown to perform worse for longer sequences
    "gpt-4-1106-preview": 64000,
}
try:
    ENCODER = tiktoken.encoding_for_model(PRETRAINED_MODEL_NAME_OR_PATH)
    logger.info("Utilize tiktoken model: {PRETRAINED_MODEL_NAME_OR_PATH}")
except Exception as exc:
    logger.exception(exc)
    sentry_sdk.capture_exception(exc)
    ENCODER = tiktoken.encoding_for_model("gpt-3.5-turbo")
    logger.info("Utilize tiktoken model: `gpt-3.5-turbo`")


def count_tokens(context, prompt, hypotheses):
    global PRETRAINED_MODEL_NAME_OR_PATH, prev_dump_datetime, requests_stats
    result = []
    texts = context + [prompt] + hypotheses
    try:
        for text in texts:
            result += [check_token_number(text, model_name=PRETRAINED_MODEL_NAME_OR_PATH)]
    except Exception as e:
        logger.exception(e)
        sentry_sdk.capture_exception(e)
        logger.info(f"Tiktoken does not contain a model: {PRETRAINED_MODEL_NAME_OR_PATH}. Use ChatGPT's one.")
        for text in texts:
            result += [check_token_number(text)]

    context_prompt_n_uttr = len(context) + 1
    # update statistics
    requests_stats += [
        {
            "input_tokens": sum(result[:context_prompt_n_uttr]),
            "output_tokens": sum(result[context_prompt_n_uttr:]),
            "api_type": os.environ.get("OPENAI_API_TYPE", "openai"),
        }
    ]

    if datetime.now() - prev_dump_datetime >= timedelta(minutes=5):
        # every 5 minutes, dump statistics
        prev_dump_datetime = dump_stats(requests_stats, statistics_fpath)
        requests_stats = []
    return


def generate_responses(context, openai_api_key, openai_org, prompt, generation_params, continue_last_uttr=False):
    outputs = []

    assert openai_api_key, logger.error("Error: OpenAI API key is not specified in env")
    openai.api_key = openai_api_key
    openai.organization = openai_org if openai_org else None

    _max_tokens = generation_params.pop("max_tokens", None)
    len_context = len(ENCODER.encode(prompt)) + sum([len(ENCODER.encode(uttr)) for uttr in context])
    if _max_tokens and len_context + _max_tokens >= MAX_TOKENS[PRETRAINED_MODEL_NAME_OR_PATH]:
        _max_tokens = None
    if openai.api_type == "azure":
        if "." in PRETRAINED_MODEL_NAME_OR_PATH:
            logger.info(f'Removing dots from model name "{PRETRAINED_MODEL_NAME_OR_PATH}".')
        generation_params["engine"] = PRETRAINED_MODEL_NAME_OR_PATH.replace(".", "")
    else:
        generation_params["model"] = PRETRAINED_MODEL_NAME_OR_PATH
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
        response = openai.ChatCompletion.create(messages=messages, max_tokens=_max_tokens, **generation_params)
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
        response = openai.Completion.create(prompt=dialog_context, max_tokens=_max_tokens, **generation_params)

    if isinstance(response, dict) and "choices" in response:
        try:
            outputs = [
                resp["message"]["content"].strip() if "message" in resp else resp.get("text", "").strip()
                for resp in response["choices"]
            ]
        except KeyError as e:
            logger.error(f"response: {response}")
            raise e
    elif isinstance(response, str):
        outputs = [response.strip()]

    if PRETRAINED_MODEL_NAME_OR_PATH not in CHAT_COMPLETION_MODELS:
        # post-processing of the responses by all models except of ChatGPT
        outputs = [GENERATIVE_ROBOT_TEMPLATE.sub("\n", resp).strip() for resp in outputs]

    count_tokens(context, prompt, outputs)
    return outputs


@app.route("/ping", methods=["POST"])
def ping():
    return "pong"


@app.route("/envvars_to_send", methods=["POST"])
def envvars_to_send():
    return jsonify(["OPENAI_API_KEY", "OPENAI_ORGANIZATION"])


@app.route("/max_tokens", methods=["POST"])
def max_tokens():
    global PRETRAINED_MODEL_NAME_OR_PATH
    return jsonify(MAX_TOKENS[PRETRAINED_MODEL_NAME_OR_PATH])


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
            outputs = generate_responses(context, openai_api_key, openai_org, prompt, config)
            responses += [outputs]

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
