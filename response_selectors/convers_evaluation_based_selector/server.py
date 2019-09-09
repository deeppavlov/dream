#!/usr/bin/env python

import json
import logging
import os
import uuid
import numpy as np

import requests
from flask import Flask, request, jsonify

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

COBOT_API_KEY = os.environ.get('COBOT_API_KEY')
COBOT_CONVERSATION_EVALUATION_SERVICE_URL =  os.environ.get('COBOT_CONVERSATION_EVALUATION_SERVICE_URL')

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_CONVERSATION_EVALUATION_SERVICE_URL is None:
    raise RuntimeError('COBOT_CONVERSATION_EVALUATION_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}


@app.route("/respond", methods=['POST'])
def respond():
    dialogs_batch = request.json["dialogs"]
    response_candidates = [dialog["utterances"][-1]["selected_skills"] for dialog in dialogs_batch]
    conversations = []
    dialog_ids = []
    selected_skill_names = []
    confidences = []

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

    result = requests.request(url=COBOT_CONVERSATION_EVALUATION_SERVICE_URL,
                              headers=headers,
                              data=json.dumps({'conversations': conversations}),
                              method='POST')
    if result.status_code != 200:
        logger.warning(
            "result status code is not 200: {}. result text: {}; result status: {}".format(result, result.text,
                                                                                           result.status_code))
        selected_skill_names = []
    else:
        result = result.json()
        # result is an array where each element is a dict with scores
        result = np.array(result["conversationEvaluationScores"])

        dialog_ids = np.array(dialog_ids)
        confidences = np.array(confidences)

        for i, dialog in enumerate(dialogs_batch):
            # curr_candidates is dict
            curr_candidates = response_candidates[i]
            # choose results which correspond curr candidates
            curr_scores = result[dialog_ids == i]
            curr_confidences = confidences[dialog_ids == i]
            best_skill_name = select_response(curr_candidates, curr_scores, curr_confidences, dialog)
            # best_response = curr_candidates[best_skill_name]["text"]
            # confidence = curr_candidates[best_skill_name]["confidence"]
            selected_skill_names.append(best_skill_name)
            logger.info(f"Choose final skill: {best_skill_name}")

    return jsonify(selected_skill_names)


def select_response(curr_candidates, curr_scores, curr_confidences, dialog):
    confidence_strength = 2
    conv_eval_strength = 0.4
    # calculate curr_scores which is an array of values-scores for each candidate
    curr_single_cores = []
    for i in range(len(curr_scores)):
        cand_scores = curr_scores[i]
        confidence = curr_confidences[i]
        skill_name = list(curr_candidates.keys())[i]
        score_conv_eval = cand_scores["isResponseOnTopic"] + \
            cand_scores["isResponseInteresting"] + \
            cand_scores["responseEngagesUser"] + \
            cand_scores["isResponseComprehensible"] - \
            cand_scores["isResponseErroneous"]
        score = conv_eval_strength*score_conv_eval + confidence_strength*confidence
        logger.info(f'Skill {skill_name} has score: {score}. Cand scores: {cand_scores}')
        curr_single_cores.append(score)
    best_id = np.argmax(curr_single_cores)
    best_skill_name = list(curr_candidates.keys())[best_id]

    while curr_candidates[best_skill_name]["text"] == "" or curr_candidates[best_skill_name]["confidence"] == 0.:
        curr_single_cores[best_id] = 0.
        best_id = np.argmax(curr_single_cores)
        best_skill_name = list(curr_candidates.keys())[best_id]
        if sum(curr_single_cores) == 0.:
            break

    return best_skill_name


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
