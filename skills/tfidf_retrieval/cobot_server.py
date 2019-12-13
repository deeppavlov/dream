#!/usr/bin/env python
import logging
import time
from data.cobot_process import check
from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    utterances_list = request.json['sentences']
    response = []
    for utterances in utterances_list:
        response = response + check(human_phrase=utterances[-1],
                                    previous_phrases=utterances[:-1])
    assert len(response[0]) == 2
    total_time = time.time() - st_time
    logger.info(f"Tfidf exec time: {total_time:.3f}s")
    logger.info(response)
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
