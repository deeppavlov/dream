#!/usr/bin/env python
import json
import logging
import numpy as np
import requests
import time
from copy import deepcopy
from os import getenv
from typing import List

import sentry_sdk
from flask import Flask, request, jsonify
from common.universal_templates import (
    if_chat_about_particular_topic,
    if_not_want_to_chat_about_particular_topic,
    if_choose_topic,
    is_switch_topic,
)
from common.utils import (
    is_toxic_or_badlisted_utterance,
    get_entities,
    get_common_tokens_in_lists_of_strings,
)


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

lets_chat_about_triggers_fname = "common/intents/lets_chat_about_triggers.json"
LETS_CHAT_ABOUT_PARTICULAR_TOPICS = json.load(open(lets_chat_about_triggers_fname))

require_action_intents_fname = "common/intents/require_action_intents.json"
REQUIRE_ACTION_INTENTS = json.load(open(require_action_intents_fname))


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


def select_response(dialog_context: List[str], hypotheses: List[dict], last_human_ann_uttr: dict, prev_bot_uttr: dict):
    scores = get_scores(dialog_context, hypotheses)
    scores = [score if hyp["skill_name"] != "dummy_skill" else score - 1 for score, hyp in zip(scores, hypotheses)]

    # ---------------------------------------------------------------------------------------------------------
    # sfc-based scaling
    try:
        speech_predictor = last_human_ann_uttr["annotations"].get("speech_function_predictor", [])
        speech_annotation = last_human_ann_uttr["annotations"].get("speech_function_classifier", [])
    except Exception as e:
        logger.error(f"speech functions failed: {e}")
    human_named_entities = get_entities(last_human_ann_uttr, only_named=True, with_labels=False)
    human_entities = get_entities(last_human_ann_uttr, only_named=False, with_labels=False)

    _human_is_switch_topic_request = is_switch_topic(last_human_ann_uttr)
    # _human_is_any_question = is_any_question_sentence_in_utterance(last_human_ann_uttr)
    # if user utterance contains any question AND requires some intent by socialbot
    _human_wants_to_chat_about_topic = (
        if_chat_about_particular_topic(last_human_ann_uttr) and "about it" not in last_human_ann_uttr["text"].lower()
    )
    _human_does_not_want_to_chat_about_topic = if_not_want_to_chat_about_particular_topic(last_human_ann_uttr)
    _human_wants_bot_to_choose_topic = if_choose_topic(last_human_ann_uttr, prev_bot_uttr)

    for hyp_id, hyp in enumerate(hypotheses):
        hyp_named_entities = get_entities(hyp, only_named=True, with_labels=False)
        hyp_entities = get_entities(hyp, only_named=False, with_labels=False)
        # identifies if candidate contains named entities from last human utterance
        _same_named_entities = len(get_common_tokens_in_lists_of_strings(hyp_named_entities, human_named_entities)) > 0
        # identifies if candidate contains all (not only named) entities from last human utterance
        _same_entities = len(get_common_tokens_in_lists_of_strings(hyp_entities, human_entities)) > 0
        _hyp_wants_to_chat_about_topic = if_chat_about_particular_topic(hyp) and "about it" not in hyp["text"].lower()

        try:
            speech_predictor_hyps = [v["prediction"] for v in speech_predictor]
            speech_predictor_scores = [v["confidence"] for v in speech_predictor]
        except TypeError:
            logger.error("Warning! The speech_predictor_classifier data is either empty or corrupt.")
            return
        try:
            speech_index = speech_predictor_hyps.index(speech_annotation)
            scores[hyp_id] += speech_predictor_scores[speech_index]
        except ValueError:
            logger.info(f"Speech function index could not be found from {hyp}, id: {hyp_id}.")

        if (
            _human_is_switch_topic_request
            or _human_does_not_want_to_chat_about_topic
            or _human_wants_bot_to_choose_topic
        ):
            # human wants to switch topic
            if len(human_named_entities) > 0 or len(human_entities) > 0:
                # if usernames entities which does not want to talk about
                if _same_named_entities or _same_entities:
                    # if hyp contains the same entities, decrease score
                    scores[hyp_id] /= 1.5
                elif len(hyp_named_entities) > 0 or len(hyp_entities) > 0:
                    # if hyp contains other entities, increase score
                    scores[hyp_id] *= 1.5
            else:
                # if user does not name entities which does not want to talk about
                if _hyp_wants_to_chat_about_topic:
                    # if hyp contains offer on chat about some entities, increase score
                    scores[hyp_id] *= 1.5
        elif _human_wants_to_chat_about_topic:
            # if user names entities which does not want to talk about
            if _same_named_entities or _same_entities:
                # if hyp contains requested entities, increase score
                scores[hyp_id] *= 1.5

    # --------------------------------------------------------------------------------------------------------------

    logger.info(f"Scores for selection:\n`{scores}`")
    result = select_response_by_scores(hypotheses, scores)[0]
    logger.info(f"ranking_and_sf_based_response_selector selected:\n`{result}`")

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
        bot_uttr = None
        try:
            bot_uttr = dialog["bot_utterances"][-1]
        except IndexError:
            logger.info("bot_uttrs is empty for this dialog")
        selected_resp = select_response(
            dialog_context,
            hypotheses,
            dialog["human_utterances"][-1],
            bot_uttr,
        )
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
    logger.info(f"ranking_and_sf_based_response_selector exec time = {total_time:.3f}s")
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
