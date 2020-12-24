#!/usr/bin/env python

from os import getenv

import json
import logging
import sentry_sdk
from flask import Flask, request, jsonify

from deeppavlov import build_model

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

gunicorn_logger = logging.getLogger('gunicorn.error')
logger.handlers = gunicorn_logger.handlers
logger.setLevel(gunicorn_logger.level)

app = Flask(__name__)

logger.info('Creating model...')

config = json.load(open("config.json"))
model = build_model(config, mode='infer', download=True)

logger.info('Creating model...DONE')


@app.route("/catch", methods=['POST'])
def catch():
    sentences = request.json['sentences']
    logger.info(f"Number of utterances: {len(sentences)}")
    results = model(sentences)
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8014)
    sess.close()
