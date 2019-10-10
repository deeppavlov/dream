#!/usr/bin/env python

from os import getenv

import logging
import sentry_sdk
import uuid
from flask import Flask, request, jsonify

from responder import Responder

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

gunicorn_logger = logging.getLogger('gunicorn.error')
logger.handlers = gunicorn_logger.handlers
logger.setLevel(gunicorn_logger.level)

app = Flask(__name__)

logger.info('Creating responder...')
responder = Responder(logger)
logger.info('Creating responder... finished')


@app.route("/respond", methods=['POST'])
def respond():
    session_id = uuid.uuid4().hex
    logger.info(f"Session_id: {session_id}")

    user_sentences = request.json['user_utterances']
    bot_sentences = request.json['bot_utterances']
    annotations = request.json['annotations']

    input = [{'user_sentence': u, 'annotation': a, 'bot_sentence': b}
             for u, a, b in zip(user_sentences, annotations, bot_sentences)]

    logger.info(f"Number of utterances: {len(user_sentences)}")
    responses = responder.respond(input)
    for r in responses:
        logger.info(f"Response:{r}")
    return jsonify(responses)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8012)
