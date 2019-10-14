#!/usr/bin/env python

import json
import logging
import os
import time
import numpy as np

import requests
from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

COBOT_API_KEY = os.environ.get('COBOT_API_KEY')
COBOT_CONVERSATION_EVALUATION_SERVICE_URL = os.environ.get('COBOT_CONVERSATION_EVALUATION_SERVICE_URL')
TOXIC_COMMENT_CLASSIFICATION_SERVICE_URL = "http://toxic_classification:8013/toxicity_annotations"
BLACKLIST_DETECTOR_URL = "http://blacklisted_words:8018/blacklisted_words"

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_CONVERSATION_EVALUATION_SERVICE_URL is None:
    raise RuntimeError('COBOT_CONVERSATION_EVALUATION_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    response_candidates = [dialog["utterances"][-1]["selected_skills"] for dialog in dialogs_batch]
    conversations = []
    dialog_ids = []
    selected_skill_names = []
    selected_texts = []
    selected_confidences = []
    confidences = []
    utterances = []

    for i, dialog in enumerate(dialogs_batch):
        for skill_name in response_candidates[i]:
            conv = dict()
            conv["currentUtterance"] = dialog["utterances"][-1]["text"]
            conv["currentResponse"] = response_candidates[i][skill_name]["text"]
            # every odd utterance is from user
            # cobot recommends to take 2 last utt for conversation evaluation service
            conv["pastUtterances"] = [uttr["text"] for uttr in dialog["utterances"][1::2]][-2:]
            # every second utterance is from bot
            conv["pastResponses"] = [uttr["text"] for uttr in dialog["utterances"][::2]][-2:]
            # collect all the conversations variants to evaluate them batch-wise
            conversations += [conv]
            dialog_ids += [i]
            confidences += [response_candidates[i][skill_name]["confidence"]]
            utterances += [response_candidates[i][skill_name]["text"]]  # all bot utterances

    # todo: refactor external service calls
    # check all possible skill responses for toxicity
    toxic_result = requests.request(url=TOXIC_COMMENT_CLASSIFICATION_SERVICE_URL,
                                    headers=headers,
                                    data=json.dumps({'sentences': utterances}),
                                    method='POST')

    if toxic_result.status_code != 200:
        msg = "Toxic classifier: result status code is not 200: {}. result text: {}; result status: {}".format(
            toxic_result, toxic_result.text, toxic_result.status_code)
        sentry_sdk.capture_message(msg)
        logger.warning(msg)
        toxicities = [0.] * len(utterances)
    else:
        toxic_result = toxic_result.json()
        toxicities = [max(res[0].values()) for res in toxic_result]

    blacklist_result = requests.request(url=BLACKLIST_DETECTOR_URL,
                                        headers=headers,
                                        data=json.dumps({'sentences': utterances}),
                                        method='POST')

    if blacklist_result.status_code != 200:
        msg = "blacklist detector: result status code is not 200: {}. result text: {}; result status: {}".format(
            blacklist_result, blacklist_result.text, blacklist_result.status_code)
        sentry_sdk.capture_message(msg)
        logger.warning(msg)
        has_blacklisted = [False] * len(utterances)
    else:
        blacklist_result = blacklist_result.json()
        has_blacklisted = [int(res['profanity']) for res in blacklist_result]

    for i, has_blisted in enumerate(has_blacklisted):
        if has_blisted:
            msg = f"response selector got candidate with blacklisted phrases:\n" \
                  f"utterance: {utterances[i]}\n" \
                  f"selected_skills: {response_candidates[dialog_ids[i]]}"
            logger.info(msg)
            sentry_sdk.capture_message(msg)

    # evaluate all possible skill responses
    result = requests.request(url=COBOT_CONVERSATION_EVALUATION_SERVICE_URL,
                              headers=headers,
                              data=json.dumps({'conversations': conversations}),
                              method='POST')
    if result.status_code != 200:
        msg = "Cobot Conversation Evaluator: result status code is \
  not 200: {}. result text: {}; result status: {}".format(result, result.text, result.status_code)
        sentry_sdk.capture_message(msg)
        logger.warning(msg)
        result = np.array([{"isResponseOnTopic": 0.,
                            "isResponseInteresting": 0.,
                            "responseEngagesUser": 0.,
                            "isResponseComprehensible": 0.,
                            "isResponseErroneous": 0.,
                            }
                           for _ in conversations])
    else:
        result = result.json()
        # result is an array where each element is a dict with scores
        result = np.array(result["conversationEvaluationScores"])

    dialog_ids = np.array(dialog_ids)
    confidences = np.array(confidences)
    toxicities = np.array(toxicities)
    has_blacklisted = np.array(has_blacklisted)

    for i, dialog in enumerate(dialogs_batch):
        # curr_candidates is dict
        curr_candidates = response_candidates[i]
        # choose results which correspond curr candidates
        curr_scores = result[dialog_ids == i]  # array of dictionaries
        curr_confidences = confidences[dialog_ids == i]  # array of float numbers

        spec = "I'm fine, thanks! Do you want to know what I can do?"
        if ('program_y' in curr_candidates) and (curr_candidates["program_y"]["text"] == spec):
            # in case we are answering to questions `how are you?`, `how are you doing?`, `how you doing?`
            best_skill_name = "program_y"
            best_text = curr_candidates[best_skill_name]["text"]
            best_confidence = curr_candidates[best_skill_name]["confidence"]
        else:
            best_skill_name, best_text, best_confidence = select_response(
                curr_candidates, curr_scores, curr_confidences,
                toxicities[dialog_ids == i], has_blacklisted[dialog_ids == i], dialog)

        selected_skill_names.append(best_skill_name)
        selected_texts.append(best_text)
        selected_confidences.append(best_confidence)
        logger.info(f"Choose final skill: {best_skill_name}")

    total_time = time.time() - st_time
    logger.info(f'convers_evaluation_selector exec time: {total_time:.3f}s')
    return jsonify(list(zip(selected_skill_names, selected_texts, selected_confidences)))


def select_response(candidates, scores, confidences, toxicities, has_blacklisted, dialog):
    confidence_strength = 2
    conv_eval_strength = 0.4
    # calculate curr_scores which is an array of values-scores for each candidate
    curr_single_cores = []

    # exclude toxic messages and messages with blacklisted phrases
    ids = (toxicities > 0.5) & (has_blacklisted > 0)
    if sum(ids) == len(toxicities):
        # the most dummy заглушка на случай, когда все абсолютно скиллы вернули токсичные ответы
        non_toxic_answers = ["I really do not know what to answer.",
                             "Sorry, probably, I din't get what you mean.",
                             "I didn't get it. Sorry"
                             ]
        non_toxic_answer = np.random.choice(non_toxic_answers)
        return None, non_toxic_answer, 1.0

    scores[ids] = {"isResponseOnTopic": 0.,
                   "isResponseInteresting": 0.,
                   "responseEngagesUser": 0.,
                   "isResponseComprehensible": 0.,
                   "isResponseErroneous": 1.,
                   }
    confidences[ids] = 0.

    for i in range(len(scores)):
        cand_scores = scores[i]
        confidence = confidences[i]
        skill_name = list(candidates.keys())[i]
        score_conv_eval = cand_scores["isResponseOnTopic"] + \
            cand_scores["isResponseInteresting"] + \
            cand_scores["responseEngagesUser"] + \
            cand_scores["isResponseComprehensible"] - \
            cand_scores["isResponseErroneous"]
        score = conv_eval_strength * score_conv_eval + confidence_strength * confidence
        logger.info(f'Skill {skill_name} has score: {score}. Toxicity: {toxicities[i]} '
                    f'Cand scores: {cand_scores}')
        curr_single_cores.append(score)
    best_id = np.argmax(curr_single_cores)
    best_skill_name = list(candidates.keys())[best_id]
    best_text = candidates[best_skill_name]["text"]
    best_confidence = candidates[best_skill_name]["confidence"]

    while candidates[best_skill_name]["text"] == "" or candidates[best_skill_name]["confidence"] == 0.:
        curr_single_cores[best_id] = 0.
        best_id = np.argmax(curr_single_cores)
        best_skill_name = list(candidates.keys())[best_id]
        best_text = candidates[best_skill_name]["text"]
        best_confidence = candidates[best_skill_name]["confidence"]
        if sum(curr_single_cores) == 0.:
            break

    return best_skill_name, best_text, best_confidence


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
