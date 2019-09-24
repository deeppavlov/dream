#!/usr/bin/env python

import json
import logging
import os
import re
import uuid
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
COBOT_DIALOGACT_SERVICE_URL =  os.environ.get('COBOT_DIALOGACT_SERVICE_URL')

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_DIALOGACT_SERVICE_URL is None:
    raise RuntimeError('COBOT_DIALOGACT_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}


@app.route("/dialogact", methods=['POST'])
def respond():
    user_states_batch = request.json['dialogs']
    user_list_sentences = [re.split("[\.\?\!]", dialog["utterances"][-1]["annotations"]["sentseg"])
                           for dialog in user_states_batch]
    user_list_sentences = [[sent.strip() for sent in sent_list if sent != ""]
                           for sent_list in user_list_sentences]

    session_id = uuid.uuid4().hex
    intents = []
    topics = []
    conversations = []
    dialog_ids = []

    for i, dialog in enumerate(user_states_batch):
        for user_sent in user_list_sentences[i]:
            conv = dict()
            conv["currentUtterance"] = user_sent
            # every odd utterance is from user
            conv["pastUtterances"] = [uttr["text"] for uttr in dialog["utterances"][1::2]]
            # every second utterance is from bot
            conv["pastResponses"] = [uttr["text"] for uttr in dialog["utterances"][::2]]
            conversations += [conv]
            dialog_ids += [i]

    result = requests.request(url=f'{COBOT_DIALOGACT_SERVICE_URL}',
                              headers=headers,
                              data=json.dumps({'conversations': conversations}),
                              method='POST')
    if result.status_code != 200:
        logger.warning("result status code is not 200: {}. result text: {}; result status: {}".format(result, result.text, result.status_code))
        intents = [[]] * len(user_states_batch)
        topics = [[]] * len(user_states_batch)
    else:
        result = result.json()
        result = np.array(result["dialogActIntents"])
        dialog_ids = np.array(dialog_ids)

        for i, sent_list in enumerate(user_list_sentences):
            logger.info(f"user_sentence: {sent_list}, session_id: {session_id}")
            curr_intents = result[dialog_ids == i]

            curr_topics = [t["topic"] for t in curr_intents]
            curr_intents = [t["dialogActIntent"] for t in curr_intents]
            intents += [curr_intents]
            topics += [curr_topics]
            logger.info(f"intent: {curr_intents}")
            logger.info(f"topic: {curr_topics}")

    return jsonify(list(zip(intents, topics)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
