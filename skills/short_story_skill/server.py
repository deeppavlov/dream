#!/usr/bin/env python

import logging
import json
from os import getenv
import sentry_sdk
from flask import Flask, request, jsonify

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE_SCENARIO, MUST_CONTINUE

from teller import Teller

STORIES_FILE = '/data/stories.json'
PHRASES_FILE = '/data/phrases.json'

status_constants = {
    "cannot": CAN_NOT_CONTINUE,
    "can": CAN_CONTINUE_SCENARIO,
    "must": MUST_CONTINUE
}

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

gunicorn_logger = logging.getLogger('gunicorn.error')
logger.handlers = gunicorn_logger.handlers
logger.setLevel(gunicorn_logger.level)

app = Flask(__name__)

logger.info('Loading stories')
try:
    stories = json.load(open(STORIES_FILE))
except json.JSONDecodeError as e:
    logger.error("Stories file is not properly encoded.")
    raise e

logger.info('Loading phrases')
try:
    phrases = json.load(open(PHRASES_FILE))
except json.JSONDecodeError as e:
    logger.error("Phrases file is not properly encoded.")
    raise e

logger.info('Creating teller')
teller = Teller(stories, phrases, status_constants, logger)

logger.info("All done!")


@app.route("/respond", methods=['POST'])
def respond():
    human_sentence = request.json['human_sentence']
    intents = request.json['intents']
    state = request.json['state']
    return jsonify([teller.tell(human_sentence, intents, state)])
