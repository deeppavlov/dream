import logging
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
    sentences = request.json.get("sentences", [])
    last_bot_utterances = request.json.get("last_bot_utterances", [])
    logger.debug(f"Sentences: {sentences}")
    logger.debug(f"Last bot utterances: {last_bot_utterances}")
    result = annotator.candidate_selection(sentences, last_bot_utterances)
    total_time = time.time() - start_time
    logger.info(f"convert-based-nli exec time: {round(total_time, 2)} sec")
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8150)
