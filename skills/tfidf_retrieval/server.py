#!/usr/bin/env python

import logging
import time
<<<<<<< HEAD
=======
import numpy as np
>>>>>>> dev
from data.process import check
from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


<<<<<<< HEAD
@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    last_utterances = request.json['sentences']
    response = []
    for last_utterance in last_utterances:
        response = response + check(last_utterance)
    assert len(response[0]) == 2
    total_time = time.time() - st_time
    logger.info(f"Tfidf exec time: {total_time:.3f}s")
    logger.info(response)
=======
@app.post("/tfidf_retrieval/")
def tfidf_retrieval():
    st_time = time.time()
    last_utterances = request.json['last_utterances']
    response = [check(last_utterance)
                for last_utterance in last_utterances
                ]
    total_time = time.time() - st_time
    logger.info(f"Tfidf exec time: {total_time:.3f}s")
>>>>>>> dev
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
