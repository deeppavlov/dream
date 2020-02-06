#!/usr/bin/env python
import logging
import time
import os
import copy
import traceback

from flask import Flask, request, jsonify
import sentry_sdk

import eliza

sentry_sdk.init(os.getenv("SENTRY_DSN"))

# VECTORIZER_FILE = os.getenv("VECTORIZER_FILE", "/global_data/*vectorizer*.zip")


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# src from https://github.com/wadetb/eliza
eliza_init_model = eliza.Eliza()
eliza_init_model.load("./doctor.txt")

# for tests
# curl -X POST "http://localhost:3000/respond" \
# -H "accept: application/json"  -H "Content-Type: application/json" \
# -d "{ \"last_utterance_batch\": [ \"what do you like\" ], \"human_utterance_history_batch\": [ [\"hi\"] ] }"
@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    last_utterance_batch = request.json.get("last_utterance_batch", [])
    human_utterance_history_batch = request.json.get("human_utterance_history_batch", [])
    logger.info(f"input data: {request.json}s")
    response = []
    try:
        for last_utterance, human_utterance_history in zip(last_utterance_batch, human_utterance_history_batch):
            eliza_model = copy.deepcopy(eliza_init_model)
            for utter in human_utterance_history:
                eliza_model.respond(utter)
            response_utter = eliza_model.respond(last_utterance)
            response_utter, confidence = (response_utter, 0.75) if response_utter != "#NOANSWER" else ("sorry", 0.0)
            response.append((response_utter, confidence))
        if not response:
            with sentry_sdk.push_scope() as scope:
                scope.set_extra("last_utterance_batch", last_utterance_batch)
                scope.set_extra("human_utterance_history_batch", human_utterance_history_batch)
                sentry_sdk.capture_message("No response in eliza")
            response = [["sorry", 0]] * len(last_utterance_batch)
    except Exception:
        with sentry_sdk.push_scope() as scope:
            scope.set_extra("last_utterance_batch", last_utterance_batch)
            scope.set_extra("human_utterance_history_batch", human_utterance_history_batch)
            scope.set_extra("traceback", traceback.format_exc())
            sentry_sdk.capture_message("Exception in eliza")
        response = [["sorry", 0]] * len(last_utterance_batch)
    assert len(response[0]) == 2
    total_time = time.time() - st_time
    logger.info(f"eliza exec time: {total_time:.3f}s")
    logger.info(response)
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
