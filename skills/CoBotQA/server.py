#!/usr/bin/env python

import json
import logging
import os
import time

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
COBOT_QA_SERVICE_URL = os.environ.get('COBOT_QA_SERVICE_URL')

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_QA_SERVICE_URL is None:
    raise RuntimeError('COBOT_QA_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    user_sentences = request.json['sentences']
    responses = []
    confidences = []
    for sent in user_sentences:
        logger.info(f"user_sentence: {sent}")
        result = requests.request(url=f'{COBOT_QA_SERVICE_URL}',
                                  headers=headers,
                                  data=json.dumps({'question': sent}),
                                  method='POST')
        if result.status_code != 200:
            logger.warning(
                f"result status code is not 200: {result}. result text: {result.text}; "
                f"result status: {result.status_code}")
            response = ''
            sentry_sdk.capture_message(
                f"CobotQA! result status code is not 200: {result}. result text: {result.text}; "
                f"result status: {result.status_code}")
        else:
            response = result.json()['response']
        responses += [response]
        logger.info(f"response: {response}")
        if len(response) > 0 and 'skill://amzn1' not in response:
            confidence = 0.97
        else:
            confidence = 0.00
        confidences += [confidence]
    total_time = time.time() - st_time
    logger.info(f'cobotqa exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
