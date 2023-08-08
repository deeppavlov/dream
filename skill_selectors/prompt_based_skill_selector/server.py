import json
import logging
import re
import time
from os import getenv

import sentry_sdk
from flask import Flask, request, jsonify
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables
from sentry_sdk.integrations.flask import FlaskIntegration


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")
GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT", 5))
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)

PROMPT_FILE = getenv("PROMPT_FILE")
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 3))
ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")

assert GENERATIVE_SERVICE_URL
assert PROMPT_FILE

with open(PROMPT_FILE, "r") as f:
    PROMPT_DICT = json.load(f)
PROMPT = PROMPT_DICT["prompt"]
GOALS_FROM_PROMPT = PROMPT_DICT.get("goals", "")

FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")


def compose_data_for_model(dialog):
    # consider N_UTTERANCES_CONTEXT last utterances
    context = dialog["utterances"][-N_UTTERANCES_CONTEXT:]
    context = [uttr.get("text", "") for uttr in context]

    if context:
        context = [re.sub(FIX_PUNCTUATION, "", x) for x in context]

    return context


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    dialogs = request.json.get("dialogs", [])
    responses = []

    for dialog in dialogs:
        dialog_context = compose_data_for_model(dialog)
        # get variables which names are in `ENVVARS_TO_SEND` (splitted by comma if many)
        # from user_utterance attributes or from environment
        human_uttr_attributes = dialog["human"]["attributes"]
        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            **human_uttr_attributes,
        )

        logger.info(f"prompt: {PROMPT}")
        logger.info(f"dialog_context: {dialog_context}")

        if len(dialog_context) > 0:
            try:
                hypotheses = send_request_to_prompted_generative_service(
                    dialog_context,
                    PROMPT,
                    GENERATIVE_SERVICE_URL,
                    GENERATIVE_SERVICE_CONFIG,
                    GENERATIVE_TIMEOUT,
                    sending_variables,
                )
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)
                hypotheses = []
        else:
            hypotheses = []
        logger.info(f"generated hypotheses: {hypotheses}")

    total_time = time.time() - st_time
    logger.info(f"prompt_based_skill_selector exec time = {total_time:.3f}s")

    return jsonify(responses)
