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
from common.utils import is_toxic_or_badlisted_utterance


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT"))
FILTER_TOXIC_OR_BADLISTED = int(getenv("FILTER_TOXIC_OR_BADLISTED"))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT"))

DEFAULT_PROMPT = json.load(open("common/prompts/response_selector.json", "r"))["prompt"]
DEFAULT_LM_SERVICE_URL = getenv("DEFAULT_LM_SERVICE_URL", "http://transformers-lm-gptjt:8161/respond")
DEFAULT_LM_SERVICE_CONFIG = getenv("DEFAULT_LM_SERVICE_CONFIG", "default_generative_config.json")
DEFAULT_LM_SERVICE_CONFIG = json.load(open(f"common/generative_configs/{DEFAULT_LM_SERVICE_CONFIG}", "r"))
KEEP_ORIGINAL_HYPOTHESIS = int(getenv("KEEP_ORIGINAL_HYPOTHESIS"))

EXTERNAL_SKILLS = ["factoid_qa", "dff_google_api_skill"]

FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")


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


def select_response(dialog, hypotheses, human_uttr_attributes):
    dialog_context = [uttr["text"] for uttr in dialog["utterances"][-N_UTTERANCES_CONTEXT:]]

    _is_prompt_based_selection = "response_selector_prompt" in human_uttr_attributes

    if human_uttr_attributes.get("return_all_hypotheses", None) and not _is_prompt_based_selection:
        return "\n".join(['"' + hyp["skill_name"] + '": "' + hyp["text"] + '"' for hyp in hypotheses])

    # get prompt from the current utterance attributes
    given_prompt = human_uttr_attributes.get("response_selector_prompt", DEFAULT_PROMPT)
    for i in range(1, len(dialog["utterances"]) + 1, 2):
        curr_prompt = dialog["utterances"][-i].get("attributes", {}).get("response_selector_prompt", DEFAULT_PROMPT)
        # checking only user utterances
        if curr_prompt != given_prompt:
            # cut context on the last user utterance utilizing the current prompt
            dialog_context = dialog_context[-i + 2 :]
            break

    try:
        ie_types = [
            "external service" if hyp["skill_name"] in EXTERNAL_SKILLS else "internal service" for hyp in hypotheses
        ]
        curr_prompt = given_prompt.replace(
            "LIST_OF_HYPOTHESES",
            "Hypotheses:\n" + "\n".join([f'"{hyp["text"]}" [{ie}]' for hyp, ie in zip(hypotheses, ie_types)]),
        )
        logger.info(f"universal_llm_based_response_selector sends dialog context to llm:\n`{dialog_context}`")
        logger.info(f"universal_llm_based_response_selector sends prompt to llm:\n`{curr_prompt}`")

        lm_service_url = human_uttr_attributes.pop("response_selector_lm_service_url", DEFAULT_LM_SERVICE_URL)
        logger.info(f"lm_service_url: {lm_service_url}")
        # this is a dictionary! not a file!
        lm_service_config = human_uttr_attributes.pop("response_selector_lm_service_config", None)

        lm_service_kwargs = human_uttr_attributes.pop("response_selector_lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = get_envvars_for_llm(lm_service_url)
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
        )
        response = send_request_to_prompted_generative_service(
            dialog_context,
            curr_prompt,
            lm_service_url,
            lm_service_config,
            GENERATIVE_TIMEOUT,
            sending_variables,
        )
        result = response[0]
        logger.info(f"universal_llm_based_response_selector received from llm:\n`{result}`")
        result = result.replace("[internal service]", "").replace("[external service]", "").strip()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        result = select_response_by_scores(hypotheses, [hyp["confidence"] for hyp in hypotheses])[0]
        logger.info("Exception in LLM's invocation. Selected a response with the highest confidence.")
    logger.info(f"universal_llm_based_response_selector selected:\n`{result}`")

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
        human_uttr_attributes = dialog["human_utterances"][-1].get("attributes", {})
        _is_prompt_based_selection = "response_selector_prompt" in human_uttr_attributes
        selected_resp = select_response(dialog, hypotheses, human_uttr_attributes)
        if selected_resp:
            best_id = find_most_similar_hypothesis(selected_resp, hypotheses)
            if human_uttr_attributes.get("return_all_hypotheses", None) and _is_prompt_based_selection:
                selected_resp += "\nHypotheses:" + "\n".join(
                    ['"' + hyp["skill_name"] + '": "' + hyp["text"] + '"' for hyp in hypotheses]
                )

            if KEEP_ORIGINAL_HYPOTHESIS:
                selected_responses.append(hypotheses[best_id].pop("text"))
            else:
                if re.match(r'^".+"$', hypotheses[best_id].get("text")):
                    pass
                elif re.match(r'^".+"$', selected_resp):
                    selected_resp = selected_resp[1:-1]
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
