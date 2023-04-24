#!/usr/bin/env python

import logging
import numpy as np
import requests
import time
from copy import deepcopy
from os import getenv

import sentry_sdk
from flask import Flask, request, jsonify
from common.utils import is_toxic_or_badlisted_utterance


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
DEFAULT_CRITERION = "the most appropriate, relevant and non-toxic"

GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT"))
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")
FILTER_TOXIC_OR_BADLISTED = int(getenv("FILTER_TOXIC_OR_BADLISTED"))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT"))
CRITERION = getenv("CRITERION", DEFAULT_CRITERION)
PROMPT = f"""Select {CRITERION} response among the hypotheses to the given dialog context. """ \
         """Return only the selected response without extra explanations."""
ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
sending_variables = {f"{var}_list": [getenv(var, None)] for var in ENVVARS_TO_SEND}
# check if at least one of the env variables is not None
if len(sending_variables.keys()) > 0 and all([var_value is None for var_value in sending_variables.values()]):
    raise NotImplementedError(
        "ERROR: All environmental variables have None values. At least one of the variables must have not None value"
    )


def filter_out_badlisted_or_toxic(hypotheses):
    clean_hypotheses = []
    for hyp in hypotheses:
        is_toxic = is_toxic_or_badlisted_utterance(hyp)
        if not is_toxic:
            clean_hypotheses += [deepcopy(hyp)]
    return clean_hypotheses


def select_response_by_scores(hypotheses, scores):
    best_id = np.argmax(scores)
    result = hypotheses[best_id]
    return result, best_id


def select_response(dialog_context, hypotheses, confidences):
    try:
        response = requests.post(
            GENERATIVE_SERVICE_URL,
            json={
                "dialog_contexts": [dialog_context],
                "prompts": [PROMPT],
                "configs": [GENERATIVE_SERVICE_CONFIG],
                **sending_variables,
            },
            timeout=GENERATIVE_TIMEOUT,
        )
        # batch of a list of one string [["this is the response"]]
        result = response.json()[0][0]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        result = select_response_by_scores(hypotheses, confidences)[0]
        logger.info(f"Exception in LLM's invocation. Selected a response with the highest confidence.")
    logger.info(f"llm_based_response_selector selected:\n`{result}`")

    return result


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    dialogs = request.json["dialogs"]

    selected_skill_names = []
    selected_responses = []
    selected_confidences = []

    for i, dialog in enumerate(dialogs):
        hypotheses = [hyp["text"] for hyp in dialog["human_utterances"][-1]["hypotheses"]]
        if FILTER_TOXIC_OR_BADLISTED:
            hypotheses = filter_out_badlisted_or_toxic(hypotheses)

        confidences = [hyp["confidence"] for hyp in hypotheses]
        skill_names = [hyp["skill_name"] for hyp in hypotheses]
        dialog_context = [uttr["text"] for uttr in dialog["utterances"][-N_UTTERANCES_CONTEXT:]]
        selected_resp = select_response(dialog_context, hypotheses, confidences)
        try:
            best_id = hypotheses.index(selected_resp)
            selected_skill_names.append(skill_names[best_id])
            selected_responses.append(selected_resp)
            selected_confidences.append(confidences[best_id])
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            logger.info("Exception in finding selected by LLM response in hypotheses. "
                        "Selected a response with the highest confidence.")
            selected_resp, best_id = select_response_by_scores(hypotheses, confidences)
            selected_skill_names.append(skill_names[best_id])
            selected_responses.append(selected_resp)
            selected_confidences.append(confidences[best_id])

    total_time = time.time() - st_time
    logger.info(f"llm_based_response_selector exec time = {total_time:.3f}s")
    return jsonify(list(zip(selected_skill_names, selected_responses, selected_confidences)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
