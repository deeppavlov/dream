import logging
import os
import time
import json
import requests
import sentry_sdk

from flask import Flask, jsonify, request
from os import getenv
from cachetools import LRUCache


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
cache = LRUCache(10000)

COBOT_API_KEY = os.environ.get("COBOT_API_KEY")
COBOT_CONVERSATION_EVALUATION_SERVICE_URL = os.environ.get("COBOT_CONVERSATION_EVALUATION_SERVICE_URL")

if COBOT_API_KEY is None:
    raise RuntimeError("COBOT_API_KEY environment variable is not set")
if COBOT_CONVERSATION_EVALUATION_SERVICE_URL is None:
    raise RuntimeError("COBOT_CONVERSATION_EVALUATION_SERVICE_URL environment variable is not set")

headers = {"Content-Type": "application/json;charset=utf-8", "x-api-key": f"{COBOT_API_KEY}"}


@app.route("/evaluate", methods=["POST"])
def respond():
    st_time = time.time()
    data = request.json
    conversations = []
    for h in data["hypotheses"]:
        conv = dict()
        conv["currentUtterance"] = data["currentUtterance"]
        conv["pastUtterances"] = data["pastUtterances"]
        conv["pastResponses"] = data["pastResponses"]
        conv["currentResponse"] = h
        conversations += [conv]
    conv_data = json.dumps({"conversations": conversations})

    try:
        if conv_data in cache:
            logger.info("got from cache")
            result = cache[conv_data]
        else:
            result = requests.request(
                url=COBOT_CONVERSATION_EVALUATION_SERVICE_URL,
                headers=headers,
                data=conv_data,
                method="POST",
                timeout=1.2,
            )
            cache[conv_data] = result
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        result = requests.Response()
        result.status_code = 504

    if result.status_code != 200:
        msg = "Cobot Conversation Evaluator: result status code is \
  not 200: {}. result text: {}; result status: {}".format(
            result, result.text, result.status_code
        )
        logger.warning(msg)
        result = [
            {
                "isResponseOnTopic": 0.0,
                "isResponseInteresting": 0.0,
                "responseEngagesUser": 0.0,
                "isResponseComprehensible": 0.0,
                "isResponseErroneous": 0.0,
            }
            for _ in conversations
        ]
    else:
        result = result.json()
        result = result["conversationEvaluationScores"]
    total_time = time.time() - st_time
    assert len(result) == len(data["hypotheses"])
    logger.info(f"cobot_conver_evaluator exec time: {total_time:.3f}s")
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
