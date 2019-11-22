#!/usr/bin/env python

import json
import logging
import os
from time import time

import requests
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ASYNC_SIZE = int(os.environ.get('ASYNC_SIZE', 10))
COBOT_API_KEY = os.environ.get('COBOT_API_KEY')
COBOT_QA_SERVICE_URL = os.environ.get('COBOT_QA_SERVICE_URL')

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_QA_SERVICE_URL is None:
    raise RuntimeError('COBOT_QA_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}


def send_cobotqa(question):
    request_body = {'question': question}
    try:
        resp = requests.request(url=COBOT_QA_SERVICE_URL,
                                headers=headers,
                                data=json.dumps(request_body),
                                method='POST',
                                timeout=10)
    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        sentry_sdk.capture_exception(e)
        logger.exception("CoBotQA Timeout")
        resp = requests.Response()
        resp.status_code = 504

    if resp.status_code != 200:
        logger.warning(
            f"result status code is not 200: {resp}. result text: {resp.text}; "
            f"result status: {resp.status_code}")
        response = ''
        sentry_sdk.capture_message(
            f"CobotQA! result status code is not 200: {resp}. result text: {resp.text}; "
            f"result status: {resp.status_code}")
    else:
        response = resp.json()['response']

    return response


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time()
    questions = request.json['sentences']
    responses = []
    confidences = []

    executor = ThreadPoolExecutor(max_workers=ASYNC_SIZE)
    for i, response in enumerate(executor.map(send_cobotqa, questions)):
        logger.info("Question: {}".format(questions[i]))
        logger.info("Response: {}".format(response))
        responses.append(response)

        if len(response) > 0 and 'skill://amzn1' not in response:
            if "let's talk about" in questions[i].lower():
                confidence = 0.5
            else:
                confidence = 0.97
        else:
            confidence = 0.00
        confidences += [confidence]

    total_time = time() - st_time
    logger.info(f'cobotqa exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
