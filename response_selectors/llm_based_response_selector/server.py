#!/usr/bin/env python

import difflib
import json
import logging
import numpy as np
import re
import time
from copy import deepcopy
from os import getenv

import sentry_sdk
from flask import Flask, request, jsonify
from common.containers import get_envvars_for_llm, is_container_running
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables
from common.response_selection import prioritize_scripted_hypotheses
from common.utils import is_toxic_or_badlisted_utterance


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
while True:
    result = is_container_running(GENERATIVE_SERVICE_URL)
    if result:
        logger.info(f"GENERATIVE_SERVICE_URL: {GENERATIVE_SERVICE_URL} is ready")
        break
    else:
        time.sleep(5)
        continue

GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)

GENERATIVE_TIMEOUT = float(getenv("GENERATIVE_TIMEOUT"))
GENERATIVE_TIMEOUT = (
    GENERATIVE_SERVICE_CONFIG.pop("timeout", GENERATIVE_TIMEOUT) if GENERATIVE_SERVICE_CONFIG else GENERATIVE_TIMEOUT
)

FILTER_TOXIC_OR_BADLISTED = int(getenv("FILTER_TOXIC_OR_BADLISTED"))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT"))
N_UTTERANCES_CONTEXT = (
    GENERATIVE_SERVICE_CONFIG.pop("n_utterances_context", N_UTTERANCES_CONTEXT)
    if GENERATIVE_SERVICE_CONFIG
    else N_UTTERANCES_CONTEXT
)

PROMPT_FILE = getenv("PROMPT_FILE")
assert PROMPT_FILE, logger.error("No prompt provided")
with open(PROMPT_FILE, "r") as f:
    PROMPT = json.load(f)["prompt"]
KEEP_ORIGINAL_HYPOTHESIS = int(getenv("KEEP_ORIGINAL_HYPOTHESIS"))
CHOOSE_HYP_BY_NUM = int(getenv("CHOOSE_HYP_BY_NUM"))

ENVVARS_TO_SEND = get_envvars_for_llm(GENERATIVE_SERVICE_URL)
EXTERNAL_SKILLS = ["factoid_qa", "dff_google_api_skill"]
assert GENERATIVE_SERVICE_URL

PRIORITIZE_SCRIPTS = int(getenv("PRIORITIZE_SCRIPTS"))


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


def select_response_full_text(dialog, hypotheses, human_uttr_attributes):
    dialog_context = [uttr["text"] for uttr in dialog["utterances"][-N_UTTERANCES_CONTEXT:]]

    if len(hypotheses) == 1:
        logger.info("Found only one hypothesis. Return it.")
        return hypotheses[0]["text"]

    hyps_without_dummy = [hyp for hyp in hypotheses if hyp["skill_name"] != "dummy_skill"]
    if len(hyps_without_dummy) == 1:
        logger.info("Found only one hypothesis apart from dummy_skill hypothesis. Return it.")
        return hyps_without_dummy[0]["text"]

    try:
        ie_types = [
            "external service" if hyp["skill_name"] in EXTERNAL_SKILLS else "internal service"
            for hyp in hyps_without_dummy
        ]
        curr_prompt = PROMPT.replace(
            "LIST_OF_HYPOTHESES",
            "Hypotheses:\n" + "\n".join([f'"{hyp["text"]}" [{ie}]' for hyp, ie in zip(hyps_without_dummy, ie_types)]),
        )
        logger.info(f"llm_based_response_selector sends dialog context to llm:\n`{dialog_context}`")
        logger.info(f"llm_based_response_selector sends prompt to llm:\n`{curr_prompt}`")

        lm_service_kwargs = human_uttr_attributes.get("response_selector", {}).get("lm_service", {}).get("kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            ENVVARS_TO_SEND,
            human_uttr_attributes,
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
        logger.info(f"llm_based_response_selector received from llm:\n`{result}`")
        result = result.replace("[internal service]", "").replace("[external service]", "").strip()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        result = select_response_by_scores(hypotheses, [hyp["confidence"] for hyp in hypotheses])[0]["text"]
        logger.info("Exception in LLM's invocation. Selected a response with the highest confidence.")
    logger.info(f"llm_based_response_selector selected:\n`{result}`")

    return result


def select_response_by_number(dialog, hypotheses, human_uttr_attributes):
    dialog_context = [uttr["text"] for uttr in dialog["utterances"][-N_UTTERANCES_CONTEXT:]]

    if len(hypotheses) == 1:
        logger.info("Found only one hypothesis. Return it.")
        return hypotheses[0]["text"]

    hyps_without_dummy = [hyp for hyp in hypotheses if hyp["skill_name"] != "dummy_skill"]
    if len(hyps_without_dummy) == 1:
        logger.info("Found only one hypothesis apart from dummy_skill hypothesis. Return it.")
        return hyps_without_dummy[0]["text"]

    try:
        ie_types = [
            "external service" if hyp["skill_name"] in EXTERNAL_SKILLS else "internal service"
            for hyp in hyps_without_dummy
        ]
        curr_prompt = PROMPT.replace(
            "LIST_OF_HYPOTHESES",
            "Hypotheses:\n"
            + "\n".join(
                [f'{i + 1}: "{hyp["text"]}" [{ie}]' for i, (hyp, ie) in enumerate(zip(hyps_without_dummy, ie_types))]
            ),
        )
        logger.info(f"llm_based_response_selector sends dialog context to llm:\n`{dialog_context}`")
        logger.info(f"llm_based_response_selector sends prompt to llm:\n`{curr_prompt}`")

        lm_service_kwargs = human_uttr_attributes.get("response_selector", {}).get("lm_service", {}).get("kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            ENVVARS_TO_SEND,
            human_uttr_attributes,
        )
        response = send_request_to_prompted_generative_service(
            dialog_context,
            curr_prompt,
            GENERATIVE_SERVICE_URL,
            GENERATIVE_SERVICE_CONFIG,
            GENERATIVE_TIMEOUT,
            sending_variables,
        )
        num_hyp = int(response[0].strip())
        logger.info(f"llm_based_response_selector received from llm:\n`{num_hyp}`")
        result = hyps_without_dummy[num_hyp - 1]["text"]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        result = select_response_by_scores(hypotheses, [hyp["confidence"] for hyp in hypotheses])[0]["text"]
        logger.info("Exception in LLM's invocation. Selected a response with the highest confidence.")
    logger.info(f"llm_based_response_selector selected:\n`{result}`")

    return result


def find_most_similar_hypothesis(final_text, hypotheses):
    scores = []
    for hyp in hypotheses:
        if hyp["skill_name"] == "dummy_skill":
            scores += [0.01]
        elif final_text in hyp["text"]:
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

        if PRIORITIZE_SCRIPTS:
            hypotheses = prioritize_scripted_hypotheses(hypotheses)

        hypotheses_texts = "\n".join([f'{h["skill_name"]} (conf={h["confidence"]}): {h["text"]}' for h in hypotheses])
        logger.info(f"Hypotheses: {hypotheses_texts}")
        human_uttr_attributes = dialog["human_utterances"][-1].get("attributes", {})
        if CHOOSE_HYP_BY_NUM:
            selected_resp = select_response_by_number(dialog, hypotheses, human_uttr_attributes)
        else:
            selected_resp = select_response_full_text(dialog, hypotheses, human_uttr_attributes)

        if selected_resp:
            best_id = find_most_similar_hypothesis(selected_resp, hypotheses)

            if KEEP_ORIGINAL_HYPOTHESIS:
                selected_responses.append(hypotheses[best_id].pop("text"))
            else:
                if re.match(r'^"[\S\s.]+"$', hypotheses[best_id].get("text")):
                    pass
                elif re.match(r'^"[\S\s.]+"$', selected_resp):
                    selected_resp = selected_resp[1:-1]
                hypotheses[best_id].pop("text")
                selected_responses.append(selected_resp)
            selected_skill_names.append(hypotheses[best_id].pop("skill_name"))
            selected_confidences.append(hypotheses[best_id].pop("confidence"))
            selected_human_attributes.append(hypotheses[best_id].pop("human_attributes", {}))
            selected_bot_attributes.append(hypotheses[best_id].pop("bot_attributes", {}))
            hypotheses[best_id].pop("annotations", {})
            selected_attributes.append(deepcopy(hypotheses[best_id]))

        else:
            logger.info("Select a response with the highest confidence.")
            selected_resp, best_id = select_response_by_scores(hypotheses, [hyp["confidence"] for hyp in hypotheses])
            selected_responses.append(hypotheses[best_id].pop("text"))
            selected_skill_names.append(hypotheses[best_id].pop("skill_name"))
            selected_confidences.append(hypotheses[best_id].pop("confidence"))
            selected_human_attributes.append(hypotheses[best_id].pop("human_attributes", {}))
            selected_bot_attributes.append(hypotheses[best_id].pop("bot_attributes", {}))
            hypotheses[best_id].pop("annotations", {})
            selected_attributes.append(deepcopy(hypotheses[best_id]))

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
