#!/usr/bin/env python

import json
import logging
import os
import uuid
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
COBOT_SENTIMENT_SERVICE_URL = os.environ.get('COBOT_SENTIMENT_SERVICE_URL')

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_SENTIMENT_SERVICE_URL is None:
    raise RuntimeError('COBOT_SENTIMENT_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}

sentiment_classes = {0: "negative", 1: "neutral", 2: "positive"}


@app.route("/sentiment", methods=['POST'])
def respond():
    st_time = time.time()
    user_sentences = request.json['sentences']
    session_id = uuid.uuid4().hex
    sentiments = []
    confidences = []
    result = requests.request(url=f'{COBOT_SENTIMENT_SERVICE_URL}',
                              headers=headers,
                              data=json.dumps({'utterances': user_sentences}),
                              method='POST').json()

    for i, sent in enumerate(user_sentences):
        logger.info(f"user_sentence: {sent}, session_id: {session_id}")
        sentiment = sentiment_classes[result["sentimentClasses"][i]["sentimentClass"]]
        confidence = result["sentimentClasses"][i]["confidence"]
        sentiments += [sentiment]
        confidences += [confidence]
        logger.info(f"sentiment: {sentiment}")
    total_time = time.time() - st_time
    logger.info(f'cobot_sentiment exec time: {total_time:.3f}s')
    return jsonify(list(zip(sentiments, confidences)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
