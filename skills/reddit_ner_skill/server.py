#!/usr/bin/env python

from os import getenv

import logging
import sentry_sdk
import uuid
from flask import Flask, request, jsonify
from database import EntityDatabase

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE_SCENARIO, MUST_CONTINUE

from linker import *

PHRASES_PATH = "/data/phrases.json"
POSTS_PATH = "/data/posts.json"
ENTITY_DATASET_PATH = "/data/entity_database.json"

status_constants = {"cannot": CAN_NOT_CONTINUE, "can": CAN_CONTINUE_SCENARIO, "must": MUST_CONTINUE}

api_key = getenv("COBOT_API_KEY")
entity_resolution_url = getenv("COBOT_ENTITY_SERVICE_URL")

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

gunicorn_logger = logging.getLogger("gunicorn.error")
logger.handlers = gunicorn_logger.handlers
logger.setLevel(gunicorn_logger.level)

app = Flask(__name__)

logger.info("Loading database")

phrases = json.load(open(PHRASES_PATH))
posts = json.load(open(POSTS_PATH))
entity_database = EntityDatabase().load(ENTITY_DATASET_PATH)

logger.info("Creating linker...")  # Create Linker
linker = Linker(entity_database, posts, phrases, entity_resolution_url, api_key, status_constants, logger)
logger.info("Creating linker... finished")


@app.route("/respond", methods=["POST"])
def respond():
    session_id = uuid.uuid4().hex
    logger.info(f"Session_id: {session_id}")

    reactions = []

    sentiment = request.json["sentiment"]
    if len(sentiment) > 0:
        sentiment = sentiment[0]["text"]  # Example: ['positive', 0.7]
        sentiment = sentiment[0] if sentiment[1] >= 0.5 else "neutral"
    else:
        sentiment = "neutral"
    logger.info(f"Sentiment: {sentiment}")

    intents = request.json["intent"][0]
    logger.info(f"Intent: {intents}")

    reaction = {"intent": None, "sentiment": sentiment}
    if intents.get("yes", {}).get("detected", 0) == 1:
        reaction["intent"] = "yes"
    if intents.get("no", {}).get("detected", 0) == 1:
        reaction["intent"] = "no"
    reactions = [reaction]
    logger.info(f"reactions: {reactions}")

    ner = [list(chain.from_iterable(chain.from_iterable(request.json["ner"])))]
    logger.info(f"ner: {ner}")

    continuations = [bool(c) for c in request.json["continuation"]]
    logger.info(f"contuniations: {continuations}")

    responses = [linker.construct_phrase(r, ec, c) for r, ec, c in zip(reactions, ner, continuations)]
    responses = [
        (phrase.strip(), 0.0 if len(phrase.strip()) == 0 else 0.90, {"can_continue": status})
        for phrase, status in responses
    ]
    logger.info(f"Responses: {responses}")

    return jsonify(responses)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8035)
