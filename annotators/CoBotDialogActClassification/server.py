#!/usr/bin/env python

import json
import logging
import os
import uuid

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
    user_sentences = [dialog["utterances"][-1]["text"] for dialog in user_states_batch]
    session_id = uuid.uuid4().hex
    intents = []
    conversations = []

    for i, dialog in enumerate(user_states_batch):
        conv = dict()
        conv["currentUtterance"] = dialog["utterances"][-1]["text"]
        # every odd utterance is from user
        conv["pastUtterances"] = [uttr["text"] for uttr in dialog["utterances"][1::2]]
        # every second utterance is from bot
        conv["pastResponses"] = [uttr["text"] for uttr in dialog["utterances"][::2]]
        conversations += [conv]

    result = requests.request(url=f'{COBOT_DIALOGACT_SERVICE_URL}',
                              headers=headers,
                              data=json.dumps({'conversations': conversations}),
                              method='POST')
    if result.status_code != 200:
        logger.warning("result status code is not 200: {}. result text: {}; result status: {}".format(result, result.text, result.status_code))
        intents = []
    else:
        result = result.json()
        for i, sent in enumerate(user_sentences):
            logger.info(f"user_sentence: {sent}, session_id: {session_id}")
            intent = result["dialogActIntents"][i]
            intents += [intent]
            logger.info(f"intent: {intent}")

    return jsonify(list(zip(intents)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
