#!/usr/bin/env python

import difflib
import json
import logging
import numpy as np
import time
from copy import deepcopy
from os import getenv

import sentry_sdk
from flask import Flask, request, jsonify
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables
from common.utils import is_toxic_or_badlisted_utterance


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

GENERATIVE_TIMEOUT = float(getenv("GENERATIVE_TIMEOUT"))
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)
FILTER_TOXIC_OR_BADLISTED = int(getenv("FILTER_TOXIC_OR_BADLISTED"))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT"))
CRITERION = getenv("CRITERION", "the most appropriate, relevant and non-toxic")
PROMPT = (
    f"""Select {CRITERION} response among the hypotheses to the given dialog context. """
    """Return only the selected response without extra explanations. """
    """Always give the lowest priority to responses that contain 'As an AI language model'/'As a chatbot' """
    """and give the highest priority to responses coming from the external services:
    """
)
ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
EXTERNAL_SKILLS = ["factoid_qa", "dff_google_api_skill"]

assert GENERATIVE_SERVICE_URL


def filter_out_badlisted_or_toxic(hypotheses):
    clean_hypotheses = []
    for hyp in hypotheses:
        is_toxic = is_toxic_or_badlisted_utterance(hyp)
        if not is_toxic:
            clean_hypotheses += [deepcopy(hyp)]
        else:
            logger.info(f"Filter out toxic candidate: {hyp['text']}")
    return clean_hypotheses


def select_response_by_scores(hypotheses, scores):
    best_id = np.argmax(scores)
    result = hypotheses[best_id]
    return result, best_id


def select_response(dialog_context, hypotheses, human_uttr_attributes):
    try:
        ie_types = [
            "external service" if hyp["skill_name"] in EXTERNAL_SKILLS else "internal service" for hyp in hypotheses
        ]
        if "transformers" in GENERATIVE_SERVICE_URL:
            curr_prompt = (
                "Hypotheses:\n"
                + "\n".join([f'"{hyp["text"]}" [{ie}]' for hyp, ie in zip(hypotheses, ie_types)])
                + "\n"
                + PROMPT
            )
        else:
            curr_prompt = (
                PROMPT
                + "\nHypotheses:\n"
                + "\n".join([f'"{hyp["text"]}" [{ie}]' for hyp, ie in zip(hypotheses, ie_types)])
            )
        logger.info(f"llm_based_response_selector sends dialog context to llm:\n`{dialog_context}`")
        logger.info(f"llm_based_response_selector sends prompt to llm:\n`{curr_prompt}`")

        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            **human_uttr_attributes,
        )
        response = send_request_to_prompted_generative_service(
            dialog_context,
            curr_prompt,
            GENERATIVE_SERVICE_URL,
            GENERATIVE_SERVICE_CONFIG,
            GENERATIVE_TIMEOUT,
            sending_variables,
        )
        result = response[0]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        result = select_response_by_scores(hypotheses, [hyp["confidence"] for hyp in hypotheses])[0]
        logger.info("Exception in LLM's invocation. Selected a response with the highest confidence.")
    logger.info(f"llm_based_response_selector selected:\n`{result}`")

    return result


def find_most_similar_hypothesis(final_text, hypotheses):
    scores = []
    for hyp in hypotheses:
        if final_text in hyp["text"]:
            scores += [0.99]
        else:
            scores += [difflib.SequenceMatcher(None, final_text, hyp["text"]).ratio()]
    logger.info(f"Scores: {scores}")
    return np.argmax(scores)


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    dialogs = request.json["dialogs"]

    selected_skill_names = []
    selected_responses = []
    selected_confidences = []
    selected_human_attributes = []
    selected_bot_attributes = []
    selected_attributes = []

    for i, dialog in enumerate(dialogs):
        hypotheses = [hyp for hyp in dialog["human_utterances"][-1]["hypotheses"]]
        if FILTER_TOXIC_OR_BADLISTED:
            hypotheses = filter_out_badlisted_or_toxic(hypotheses)
        hypotheses_texts = "\n".join([f'{h["skill_name"]} (conf={h["confidence"]}): {h["text"]}' for h in hypotheses])
        logger.info(f"Hypotheses: {hypotheses_texts}")
        dialog_context = [uttr["text"] for uttr in dialog["utterances"][-N_UTTERANCES_CONTEXT:]]
        selected_resp = select_response(
            dialog_context, hypotheses, dialog["human_utterances"][-1].get("attributes", {})
        )
        if selected_resp:
            best_id = find_most_similar_hypothesis(selected_resp, hypotheses)
            hypotheses[best_id].pop("text")
            selected_responses.append(selected_resp)
            selected_skill_names.append(hypotheses[best_id].pop("skill_name"))
            selected_confidences.append(hypotheses[best_id].pop("confidence"))
            selected_human_attributes.append(hypotheses[best_id].pop("human_attributes", {}))
            selected_bot_attributes.append(hypotheses[best_id].pop("bot_attributes", {}))
            hypotheses[best_id].pop("annotations", {})
            selected_attributes.append(hypotheses[best_id])

        else:
            logger.info("Select a response with the highest confidence.")
            selected_resp, best_id = select_response_by_scores(hypotheses, [hyp["confidence"] for hyp in hypotheses])
            selected_responses.append(hypotheses[best_id].pop("text"))
            selected_skill_names.append(hypotheses[best_id].pop("skill_name"))
            selected_confidences.append(hypotheses[best_id].pop("confidence"))
            selected_human_attributes.append(hypotheses[best_id].pop("human_attributes", {}))
            selected_bot_attributes.append(hypotheses[best_id].pop("bot_attributes", {}))
            hypotheses[best_id].pop("annotations", {})
            selected_attributes.append(hypotheses[best_id])

    total_time = time.time() - st_time
    logger.info(f"llm_based_response_selector exec time = {total_time:.3f}s")
    return jsonify(
        list(
            zip(
                selected_skill_names,
                selected_responses,
                selected_confidences,
                selected_human_attributes,
                selected_bot_attributes,
                selected_attributes,
            )
        )
    )


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
