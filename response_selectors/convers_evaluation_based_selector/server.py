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
    dialogs_batch = request.json['states_batch']["dialogs"]
    response_candidates = [dialog["utterances"][-1]["selected_skills"] for dialog in dialogs_batch]
    session_id = uuid.uuid4().hex
    conversations = []
    dialog_ids = []
    selected_skill_names = []
    utterances = []
    confidences = []

    for i, dialog in enumerate(dialogs_batch):
        for skill_name in response_candidates[i]:
            conv = dict()
            conv["currentUtterance"] = dialog["utterances"][-1]["text"]
            conv["currentResponse"] = response_candidates[i][skill_name]["text"]
            # every odd utterance is from user
            conv["pastUtterances"] = [uttr["text"] for uttr in dialog["utterances"][1::2]]
            # every second utterance is from bot
            conv["pastResponses"] = [uttr["text"] for uttr in dialog["utterances"][::2]]
            # collect all the conversations variants to evaluate them batch-wise
            conversations += [conv]
            dialog_ids += [i]
    logger.info(conversations)
    result = requests.request(url=COBOT_CONVERSATION_EVALUATION_SERVICE_URL,
                              headers=headers,
                              data=json.dumps({'conversations': conversations}),
                              method='POST').json()
    # result is an array where each element is a dict with scores
    result = np.array(result["conversationEvaluationScores"])

    dialog_ids = np.array(dialog_ids)

    for i, dialog in enumerate(dialogs_batch):
        # curr_candidates is dict
        curr_candidates = response_candidates[i]
        # choose results which correspond curr candidates
        curr_scores = result[dialog_ids == i]
        best_id = select_response(curr_candidates, curr_scores, dialog)
        best_skill_name = list(response_candidates[i].keys())[best_id]
        best_response = curr_candidates[best_skill_name]["text"]
        confidence = curr_candidates[best_skill_name]["confidence"]

        selected_skill_names.append(best_skill_name)
        utterances.append(best_response)
        confidences.append(confidence)

        logger.info(f"Choose final skill: {best_skill_name}")

    return jsonify(list(zip(selected_skill_names, utterances, confidences)))


def select_response(curr_candidates, curr_scores, dialog):
    # calculate curr_scores which is an array of values-scores for each candidate
    curr_single_cores = [(cand_scores["isResponseOnTopic"] + cand_scores["isResponseInteresting"] +
                          cand_scores["responseEngagesUser"] + cand_scores["isResponseComprehensible"] -
                          cand_scores["isResponseErroneous"])
                         for cand_scores in curr_scores]

    best_id = np.argmax(curr_single_cores)
    return best_id


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
