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

SENTENCE_RANKER_ANNOTATION_NAME = getenv("SENTENCE_RANKER_ANNOTATION_NAME")
SENTENCE_RANKER_SERVICE_URL = getenv("SENTENCE_RANKER_SERVICE_URL")
SENTENCE_RANKER_TIMEOUT = float(getenv("SENTENCE_RANKER_TIMEOUT"))
FILTER_TOXIC_OR_BADLISTED = int(getenv("FILTER_TOXIC_OR_BADLISTED"))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT"))
assert SENTENCE_RANKER_ANNOTATION_NAME or SENTENCE_RANKER_SERVICE_URL, logger.error(
    "Ranker service URL or annotator name should be given"
)


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


def get_scores(dialog_context, hypotheses):
    if all([SENTENCE_RANKER_ANNOTATION_NAME in hyp.get("annotations", {}) for hyp in hypotheses]):
        scores = [hyp.get("annotations", {}).get(SENTENCE_RANKER_ANNOTATION_NAME, 0.0) for hyp in hypotheses]
        logger.info("Selected a response via Sentence Ranker Annotator.")
    else:
        try:
            dialog_context = "\n".join(dialog_context)
            pairs = [[dialog_context, hyp["text"]] for hyp in hypotheses]
            scores = requests.post(
                SENTENCE_RANKER_SERVICE_URL,
                json={"sentence_pairs": pairs},
                timeout=SENTENCE_RANKER_TIMEOUT,
            ).json()
            scores = np.array(scores[0]["batch"])
            logger.info("Selected a response via Sentence Ranker Service.")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            scores = [hyp["confidence"] for hyp in hypotheses]
            logger.exception(e)
            logger.info("Selected a response via Confidence.")
    return scores


def select_response(dialog_context, hypotheses):
    scores = get_scores(dialog_context, hypotheses)
    scores = [score if hyp["skill_name"] != "dummy_skill" else score - 1 for score, hyp in zip(scores, hypotheses)]
    logger.info(f"Scores for selection:\n`{scores}`")
    result = select_response_by_scores(hypotheses, scores)[0]
    logger.info(f"ranking_based_response_selector selected:\n`{result}`")

    return result


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
        selected_resp = select_response(dialog_context, hypotheses)
        try:
            best_id = hypotheses.index(selected_resp)

            selected_responses.append(hypotheses[best_id].pop("text"))
            selected_skill_names.append(hypotheses[best_id].pop("skill_name"))
            selected_confidences.append(hypotheses[best_id].pop("confidence"))
            selected_human_attributes.append(hypotheses[best_id].pop("human_attributes", {}))
            selected_bot_attributes.append(hypotheses[best_id].pop("bot_attributes", {}))
            hypotheses[best_id].pop("annotations", {})
            selected_attributes.append(hypotheses[best_id])

        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            logger.info(
                "Exception in finding selected response in hypotheses. "
                "Selected a response with the highest confidence."
            )
            selected_resp, best_id = select_response_by_scores(hypotheses, [hyp["confidence"] for hyp in hypotheses])

            selected_responses.append(hypotheses[best_id].pop("text"))
            selected_skill_names.append(hypotheses[best_id].pop("skill_name"))
            selected_confidences.append(hypotheses[best_id].pop("confidence"))
            selected_human_attributes.append(hypotheses[best_id].pop("human_attributes", {}))
            selected_bot_attributes.append(hypotheses[best_id].pop("bot_attributes", {}))
            hypotheses[best_id].pop("annotations", {})
            selected_attributes.append(hypotheses[best_id])

    total_time = time.time() - st_time
    logger.info(f"ranking_based_response_selector exec time = {total_time:.3f}s")
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
