#!/usr/bin/env python

import json
import logging
import os
import time
import numpy as np

import requests
from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

COBOT_API_KEY = os.environ.get("COBOT_API_KEY")
COBOT_DIALOGACT_SERVICE_URL = os.environ.get("COBOT_DIALOGACT_SERVICE_URL")

if COBOT_API_KEY is None:
    raise RuntimeError("COBOT_API_KEY environment variable is not set")
if COBOT_DIALOGACT_SERVICE_URL is None:
    raise RuntimeError("COBOT_DIALOGACT_SERVICE_URL environment variable is not set")

headers = {"Content-Type": "application/json;charset=utf-8", "x-api-key": f"{COBOT_API_KEY}"}


def get_result(request):
    st_time = time.time()
    utterances_histories = request.json["utterances_histories"]
    intents = []
    topics = []
    conversations = []
    dialog_ids = []

    for i, dialog in enumerate(utterances_histories):
        # dialog is a list of replies. each reply is a list of sentences
        for user_sent in dialog[-1]:
            conv = dict()
            logger.info("User sent: {}".format(user_sent))
            conv["currentUtterance"] = user_sent
            # every odd utterance is from user
            conv["pastUtterances"] = [" ".join(list_sent) for list_sent in dialog[:-1][1::2][-2:]]
            # every second utterance is from bot
            conv["pastResponses"] = [" ".join(list_sent) for list_sent in dialog[:-1][::2][-2:]]
            conversations += [conv]
            dialog_ids += [i]
    try:
        result = requests.request(
            url=f"{COBOT_DIALOGACT_SERVICE_URL}",
            headers=headers,
            data=json.dumps({"conversations": conversations}),
            method="POST",
            timeout=1,
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        result = requests.Response()
        result.status_code = 504

    if result.status_code != 200:
        logger.warning(
            "result status code is not 200: {}. result text: {}; result status: {}".format(
                result, result.text, result.status_code
            )
        )
        intents = [[]] * len(utterances_histories)
        topics = [[]] * len(utterances_histories)
    else:
        result = result.json()
        result = np.array(result["dialogActIntents"])
        dialog_ids = np.array(dialog_ids)

        for i, sent_list in enumerate(utterances_histories):
            logger.info(f"user_sentence: {sent_list}")
            curr_intents = result[dialog_ids == i]

            curr_topics = [t["topic"] for t in curr_intents]
            curr_intents = [t["dialogActIntent"] for t in curr_intents]
            intents += [curr_intents]
            topics += [curr_topics]
            logger.info(f"intent: {curr_intents}")
            logger.info(f"topic: {curr_topics}")

    total_time = time.time() - st_time
    logger.info(f"cobot_dialogact exec time: {total_time:.3f}s")
    return list(zip(intents, topics))


@app.route("/dialogact", methods=["POST"])
def respond():
    result = get_result(request)
    return jsonify(result)


@app.route("/dialogact_batch", methods=["POST"])
def respond_batch():
    result = get_result(request)
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
