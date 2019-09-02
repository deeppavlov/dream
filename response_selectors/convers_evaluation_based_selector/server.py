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
    response_candidates = request.json['response_candidates']
    user_states_batch = request.json['states_batch']
    session_id = uuid.uuid4().hex
    conversations = []
    dialog_ids = []
    selected_skill_names = []
    utterances = []
    confidences = []

    characteristics = ["isResponseOnTopic", "isResponseInteresting", "responseEngagesUser",
                       "isResponseErroneous", "isResponseComprehensible"]
    skill_names = response_candidates.keys()
    logger.info("Skill names: {}".format(skill_names))

    for i, dialog in enumerate(user_states_batch):
        for resp in response_candidates[i]:
            conv = dict()
            conv["currentUtterance"] = dialog["utterances"][-1]["text"]
            conv["currentResponse"] = resp
            # every odd utterance is from user
            conv["pastUtterances"] = [uttr["text"] for uttr in dialog["utterances"][1::2]]
            # every second utterance is from bot
            conv["pastResponses"] = [uttr["text"] for uttr in dialog["utterances"][::2]]
            # collect all the conversations variants to evaluate them batch-wise
            conversations += [conv]
            dialog_ids += [i]

    result = requests.request(url=COBOT_CONVERSATION_EVALUATION_SERVICE_URL,
                              headers=headers,
                              data=json.dumps({'conversations': [conversations]}),
                              method='POST').json()
    # result is an array where each element is a dict with scores
    result = np.array(result["conversationEvaluationScores"])

    dialog_ids = np.array(dialog_ids)

    for i, dialog in enumerate(user_states_batch):
        sent = dialog["utterances"][-1]["text"]
        logger.info(f"user_sentence: {sent}, session_id: {session_id}")
        # curr_cands is dict
        curr_cands = response_candidates[i]
        # choose results which correspond curr candidates -> result[dialog_ids == i]
        best_id, confidence = select_response(curr_cands, result[dialog_ids == i], dialog)
        best_skill_name = skill_names[best_id]
        best_response = curr_cands[best_skill_name]

        selected_skill_names.append(best_skill_name)
        utterances.append(best_response)
        confidences.append(confidence)

        logger.info(f"Choose final skill: {best_skill_name}")

    return jsonify(list(zip(selected_skill_names, utterances, confidences)))


def select_response(curr_candidates: dict, curr_scores: np.ndarray[dict], state: dict):
    # calculate curr_scores which is an array of values-scores for each candidate
    curr_scores = [sum(cand_scores.values()) for cand_scores in curr_scores]
    # choose candidate with max score
    confidence = np.amax(curr_scores)
    best_id = np.argmax(curr_scores)
    return best_id, confidence


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
