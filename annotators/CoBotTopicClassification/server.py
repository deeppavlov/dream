#!/usr/bin/env python

import json
import logging
import os
import uuid
import re
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
COBOT_TOPICS_SERVICE_URL = os.environ.get('COBOT_TOPICS_SERVICE_URL')

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_TOPICS_SERVICE_URL is None:
    raise RuntimeError('COBOT_TOPICS_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}


@app.route("/topics", methods=['POST'])
def respond():
    user_states_batch = request.json['dialogs']
    user_list_sentences = [re.split("[\.\?\!]", dialog["utterances"][-1]["annotations"]["sentseg"])
                           for dialog in user_states_batch]
    user_list_sentences = [[sent.strip() for sent in sent_list if sent != ""]
                           for sent_list in user_list_sentences]

    user_sentences = []
    dialog_ids = []
    for i, sent_list in enumerate(user_list_sentences):
        for sent in sent_list:
            user_sentences.append(sent)
            dialog_ids += [i]

    session_id = uuid.uuid4().hex
    topics = []
    confidences = []
    result = requests.request(url=f'{COBOT_TOPICS_SERVICE_URL}',
                              headers=headers,
                              data=json.dumps({'utterances': user_sentences}),
                              method='POST')

    if result.status_code != 200:
        msg = "result status code is not 200: {}. result text: {}; result status: {}".format(result, result.text,
                                                                                             result.status_code)
        sentry_sdk.capture_message(msg)
        logger.warning(msg)
        selected_skill_names = []
    else:
        result = result.json()
        # result is an array where each element is a dict with scores
        result = np.array(result["topics"])
        dialog_ids = np.array(dialog_ids)

        for i, sent_list in enumerate(user_list_sentences):
            logger.info(f"user_sentence: {sent_list}, session_id: {session_id}")
            curr_topics = result[dialog_ids == i]
            logger.info(f"curr_topics: {curr_topics}")

            curr_topics = [t["topicClass"] for t in curr_topics]
            topics += [curr_topics]
            logger.info(f"topic: {curr_topics}")

    return jsonify(topics)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
