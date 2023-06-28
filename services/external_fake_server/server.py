import logging
import time
from os import getenv

import sentry_sdk

from flask import Flask, request, jsonify


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/ping", methods=["POST"])
def ping():
    return "pong"


@app.route("/return_response", methods=["POST"])
def return_response():
    st_time = time.time()
    message = request.json.get("payload", None)
    dialog_id = request.json.get("dialog_id", None)
    logger.info(f"fake-external-server got message: {message}, dialog_id: {dialog_id}")
    if message and dialog_id:
        results = {"response": "Success!", "confidence": 0.9}
    else:
        results = {"response": "", "confidence": 0.0}
    logger.info(f"fake-external-server `return_response` results: {results}")
    total_time = time.time() - st_time
    logger.info(f"fake-external-server `return_response` exec time: {total_time:.3f}s")
    return jsonify(results)
