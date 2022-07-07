import logging
import os
import time

import sentry_sdk
from flask import Flask, jsonify, request

from deeppavlov import build_model

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

config_name = os.getenv("CONFIG")

try:
    spelling_preprocessing_model = build_model(config_name, download=True)
    r = "я ге видел малако"
    logger.info(f"Original: {r}. Corrected: {spelling_preprocessing_model([r])}")
    logger.info("spelling_preprocessing model is loaded.")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    sentences = request.json["sentences"]
    sentences = [text.lower() for text in sentences]
    corrected_sentences = spelling_preprocessing_model(sentences)

    total_time = time.time() - st_time
    logger.info(f"spelling_preprocessing exec time: {total_time:.3f}s")
    return jsonify(corrected_sentences)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8074)
