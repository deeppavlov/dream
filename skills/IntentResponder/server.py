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

    dialogs = request.json['dialogs']
    responses = []
    confidences = []

    for dialog in dialogs:
        logger.info(f"User utterance: {dialog['utterances'][-1]['text']}")
        logger.info(f"Called intents: {dialog['called_intents']}")
        response, confidence = responder.respond(dialog)
        logger.info(f"Response: {response}")
        responses.append(response)
        confidences.append(confidence)

    return jsonify(list(zip(responses, confidences)))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8012)
