
import logging
from os import getenv
from time import time

import numpy as np
import sentry_sdk
from flask import Flask, request, jsonify
from deeppavlov import build_model


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


try:
    faq_model = build_model()
except Exception as e:
    logger.warning(e)
    sentry_sdk.capture_message(e)

 
@app.route("/respond", methods=["POST"])
def respond():
    st_time = time()
    dialogs = request.json["dialogs"]
    responses = []
    confidences = []
    attributes = []

    for dialog, curr_topic, curr_status, result in zip(dialogs, topics, statuses, curr_news_samples):

        responses.append(response)
        confidences.append(confidence)
        attributes.append(attr)

    total_time = time() - st_time
    logger.info(f"faq-skill exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences, attributes)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
