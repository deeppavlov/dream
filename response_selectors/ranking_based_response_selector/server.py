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

SENTENCE_RANKER_SERVICE_URL = getenv("SENTENCE_RANKER_SERVICE_URL")
SENTENCE_RANKER_TIMEOUT = int(getenv("SENTENCE_RANKER_TIMEOUT"))
FILTER_TOXIC_OR_BADLISTED = int(getenv("FILTER_TOXIC_OR_BADLISTED"))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT"))


def filter_out_badlisted_or_toxic(hypotheses):
    clean_hypotheses = []
    for hyp in hypotheses:
        is_toxic = is_toxic_or_badlisted_utterance(hyp)
        if not is_toxic:
            clean_hypotheses += [deepcopy(hyp)]
    return clean_hypotheses


def select_response_by_confidence(hypotheses, confidences):
    best_id = np.argmax(confidences)
    result = hypotheses[best_id]
    return result, best_id


def select_response(dialog_context, hypotheses, confidences):
    try:
        dialog_context = "\n".join(dialog_context)
        pairs = [[dialog_context, hyp["text"]] for hyp in hypotheses]
        scores = requests.post(
            SENTENCE_RANKER_SERVICE_URL,
            json={"sentence_pairs": pairs},
            timeout=SENTENCE_RANKER_TIMEOUT,
        ).json()
        scores = np.array(scores[0]["batch"])
        result = select_response_by_confidence(hypotheses, scores)[0]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        result = select_response_by_confidence(hypotheses, confidences)[0]
        logger.info(f"Exception in LLM's invocation. Selected a response with the highest confidence.")
    logger.info(f"ranking_based_response_selector selected:\n`{result}`")

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
            selected_resp, best_id = select_response_by_confidence(hypotheses, confidences)
            selected_skill_names.append(skill_names[best_id])
            selected_responses.append(selected_resp)
            selected_confidences.append(confidences[best_id])

    total_time = time.time() - st_time
    logger.info(f"ranking_based_response_selector exec time = {total_time:.3f}s")
    return jsonify(list(zip(selected_skill_names, selected_responses, selected_confidences)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
