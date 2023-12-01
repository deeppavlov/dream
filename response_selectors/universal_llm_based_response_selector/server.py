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
from common.containers import get_envvars_for_llm
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables
from common.response_selection import prioritize_scripted_hypotheses
from common.utils import is_toxic_or_badlisted_utterance


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DEFAULT_LM_SERVICE_TIMEOUT = float(getenv("DEFAULT_LM_SERVICE_TIMEOUT"))
FILTER_TOXIC_OR_BADLISTED = int(getenv("FILTER_TOXIC_OR_BADLISTED"))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT"))

DEFAULT_PROMPT = json.load(open("common/prompts/response_selector.json", "r"))["prompt"]
DEFAULT_LM_SERVICE_URL = getenv("DEFAULT_LM_SERVICE_URL", "http://transformers-lm-gptjt:8161/respond")
DEFAULT_LM_SERVICE_CONFIG = getenv("DEFAULT_LM_SERVICE_CONFIG", "default_generative_config.json")
DEFAULT_LM_SERVICE_CONFIG = json.load(open(f"common/generative_configs/{DEFAULT_LM_SERVICE_CONFIG}", "r"))
KEEP_ORIGINAL_HYPOTHESIS = int(getenv("KEEP_ORIGINAL_HYPOTHESIS"))
CHOOSE_HYP_BY_NUM = int(getenv("CHOOSE_HYP_BY_NUM"))
PRIORITIZE_SCRIPTS = int(getenv("PRIORITIZE_SCRIPTS"))

EXTERNAL_SKILLS = ["factoid_qa", "dff_google_api_skill"]


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
    dialog_context = [uttr["text"] for uttr in dialog["utterances"]]

    if len(hypotheses) == 1:
        logger.info("Found only one hypothesis. Return it.")
        return hypotheses[0]["text"]

    hyps_without_dummy = [hyp for hyp in hypotheses if hyp["skill_name"] != "dummy_skill"]
    if len(hyps_without_dummy) == 1:
        logger.info("Found only one hypothesis apart from dummy_skill hypothesis. Return it.")
        return hyps_without_dummy[0]["text"]

    _response_selector = human_uttr_attributes.get("response_selector", {})
    _is_prompt_based_selection = "prompt" in _response_selector

    if not _is_prompt_based_selection:
        # in case of skill selector's debug, we chose response for the dialog context by scores
        result = select_response_by_scores(hypotheses, [hyp["confidence"] for hyp in hypotheses])[0]["text"]
        logger.info("Select by confidences because it is not Response Selector's Debug")
        return result

    # get prompt from the current utterance attributes
    given_prompt = _response_selector.get("prompt", DEFAULT_PROMPT)
    for i in range(1, len(dialog["utterances"]) + 1, 2):
        curr_prompt = (
            dialog["utterances"][-i].get("attributes", {}).get("response_selector", {}).get("prompt", DEFAULT_PROMPT)
        )
        # checking only user utterances
        if curr_prompt != given_prompt:
            # cut context on the last user utterance utilizing the current prompt
            dialog_context = dialog_context[-i + 2 :]
            break

    try:
        ie_types = [
            "external service" if hyp["skill_name"] in EXTERNAL_SKILLS else "internal service"
            for hyp in hyps_without_dummy
        ]
        curr_prompt = given_prompt.replace(
            "LIST_OF_HYPOTHESES",
            "Hypotheses:\n" + "\n".join([f'"{hyp["text"]}" [{ie}]' for hyp, ie in zip(hyps_without_dummy, ie_types)]),
        )
        logger.info(f"universal_llm_based_response_selector sends dialog context to llm:\n`{dialog_context}`")
        logger.info(f"universal_llm_based_response_selector sends prompt to llm:\n`{curr_prompt}`")

        lm_service_url = _response_selector.get("lm_service", {}).get("url", DEFAULT_LM_SERVICE_URL)
        logger.info(f"lm_service_url: {lm_service_url}")
        # this is a dictionary! not a file!
        lm_service_config = _response_selector.get("lm_service", {}).get("config", None)

        lm_service_kwargs = _response_selector.get("lm_service", {}).get("kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = get_envvars_for_llm(lm_service_url)
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            human_uttr_attributes,
        )
        lm_service_timeout = (
            lm_service_config.pop("timeout", DEFAULT_LM_SERVICE_TIMEOUT)
            if lm_service_config
            else DEFAULT_LM_SERVICE_TIMEOUT
        )
        n_utterances_context = (
            lm_service_config.pop("n_utterances_context", N_UTTERANCES_CONTEXT)
            if lm_service_config
            else N_UTTERANCES_CONTEXT
        )

        response = send_request_to_prompted_generative_service(
            dialog_context[-n_utterances_context:],
            curr_prompt,
            lm_service_url,
            lm_service_config,
            lm_service_timeout,
            sending_variables,
        )
        result = response[0]
        logger.info(f"universal_llm_based_response_selector received from llm:\n`{result}`")
        result = result.replace("[internal service]", "").replace("[external service]", "").strip()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        result = select_response_by_scores(hypotheses, [hyp["confidence"] for hyp in hypotheses])[0]["text"]
        logger.info("Exception in LLM's invocation. Selected a response with the highest confidence.")
    logger.info(f"universal_llm_based_response_selector selected:\n`{result}`")

    return result


def select_response_by_number(dialog, hypotheses, human_uttr_attributes):
    dialog_context = [uttr["text"] for uttr in dialog["utterances"]]

    if len(hypotheses) == 1:
        logger.info("Found only one hypothesis. Return it.")
        return hypotheses[0]["text"]

    hyps_without_dummy = [hyp for hyp in hypotheses if hyp["skill_name"] != "dummy_skill"]
    if len(hyps_without_dummy) == 1:
        logger.info("Found only one hypothesis apart from dummy_skill hypothesis. Return it.")
        return hyps_without_dummy[0]["text"]

    _response_selector = human_uttr_attributes.get("response_selector", {})
    _is_prompt_based_selection = "prompt" in _response_selector

    if not _is_prompt_based_selection:
        # in case of skill selector's debug, we chose response for the dialog context by scores
        result = select_response_by_scores(hypotheses, [hyp["confidence"] for hyp in hypotheses])[0]["text"]
        logger.info("Select by confidences because it is not Response Selector's Debug")
        return result

    # get prompt from the current utterance attributes
    given_prompt = _response_selector.get("prompt", DEFAULT_PROMPT)
    for i in range(1, len(dialog["utterances"]) + 1, 2):
        curr_prompt = (
            dialog["utterances"][-i].get("attributes", {}).get("response_selector", {}).get("prompt", DEFAULT_PROMPT)
        )
        # checking only user utterances
        if curr_prompt != given_prompt:
            # cut context on the last user utterance utilizing the current prompt
            dialog_context = dialog_context[-i + 2 :]
            break

    try:
        ie_types = [
            "external service" if hyp["skill_name"] in EXTERNAL_SKILLS else "internal service"
            for hyp in hyps_without_dummy
        ]
        curr_prompt = given_prompt.replace(
            "LIST_OF_HYPOTHESES",
            "Hypotheses:\n"
            + "\n".join(
                [f'{i + 1}: "{hyp["text"]}" [{ie}]' for i, (hyp, ie) in enumerate(zip(hyps_without_dummy, ie_types))]
            ),
        )
        logger.info(f"universal_llm_based_response_selector sends dialog context to llm:\n`{dialog_context}`")
        logger.info(f"universal_llm_based_response_selector sends prompt to llm:\n`{curr_prompt}`")

        lm_service_url = _response_selector.get("lm_service", {}).get("url", DEFAULT_LM_SERVICE_URL)
        logger.info(f"lm_service_url: {lm_service_url}")
        # this is a dictionary! not a file!
        lm_service_config = _response_selector.get("lm_service", {}).get("config", None)

        lm_service_kwargs = _response_selector.get("lm_service", {}).get("kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = get_envvars_for_llm(lm_service_url)
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            human_uttr_attributes,
        )
        lm_service_timeout = (
            lm_service_config.pop("timeout", DEFAULT_LM_SERVICE_TIMEOUT)
            if lm_service_config
            else DEFAULT_LM_SERVICE_TIMEOUT
        )
        n_utterances_context = (
            lm_service_config.pop("n_utterances_context", N_UTTERANCES_CONTEXT)
            if lm_service_config
            else N_UTTERANCES_CONTEXT
        )

        response = send_request_to_prompted_generative_service(
            dialog_context[-n_utterances_context:],
            curr_prompt,
            lm_service_url,
            lm_service_config,
            lm_service_timeout,
            sending_variables,
        )
        num_hyp = response[0].strip()
        logger.info(f"llm_based_response_selector received from llm:\n`{num_hyp}`")
        result = hyps_without_dummy[num_hyp - 1]["text"]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        result = select_response_by_scores(hypotheses, [hyp["confidence"] for hyp in hypotheses])[0]["text"]
        logger.info("Exception in LLM's invocation. Selected a response with the highest confidence.")
    logger.info(f"universal_llm_based_response_selector selected:\n`{result}`")

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
    logger.info(f"universal_llm_based_response_selector exec time = {total_time:.3f}s")
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
