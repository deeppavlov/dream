import logging
import numpy as np
import time
from os import getenv

from convert_annotator import ConveRTAnnotator
import sentry_sdk
from flask import Flask, jsonify, request


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

annotator = ConveRTAnnotator()
logger.info("Annotator is loaded.")


@app.route("/batch_model", methods=["POST"])
def respond_batch():
    start_time = time.time()
    candidates = request.json.get("candidates", [])
    history = request.json.get("history", [])
    logger.info(f"Candidates: {candidates}")
    logger.info(f"History: {history}")
    result = annotator.candidate_selection(candidates, history)
    total_time = time.time() - start_time
    logger.info(f"Annotator candidate prediction time: {total_time: .3f}s")
    return jsonify([{"batch": result}])


@app.route("/encode", methods=["POST"])
def respond_encode():
    start_time = time.time()
    response = request.json.get("sentences", [])
    logger.info(f"sentence: {response}")
    result = annotator.response_encoding(response)
    total_time = time.time() - start_time
    logger.info(f"Annotator response encoding time: {total_time: .3f}s")
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8137)
