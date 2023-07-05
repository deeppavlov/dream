import logging
import time
from os import getenv

import sentry_sdk
import requests
from flask import Flask, jsonify, request


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

SUMMARIZATION_SERVICE_URL = getenv("SUMMARIZATION_SERVICE_URL")
logger.info(f"summarization-annotator considered summarizer: {SUMMARIZATION_SERVICE_URL}")


def get_summary(dialog):
    summary = []
    if len(dialog) != 11:
        logger.info(f"summarization-annotator is not ready to summarize dialog as the length of unsummarized dialog is {len(dialog)} != 11")
        return summary

    logger.info(f"summarization-annotator is ready to summarize dialog as the length of unsummarized dialog is 11")
    dialog = dialog[:6]
    for i in range(len(dialog)):
        if i % 2 == 0:
            dialog[i] = 'User: ' + dialog[i]
        else:
            dialog[i] = 'Bot: ' + dialog[i]
    dialog = ['\n'.join(dialog)]
    logger.info(f"summarization-annotator will summarize this: {dialog}")

    try:
        summary = requests.post(SUMMARIZATION_SERVICE_URL, json={"sentences": dialog}, timeout=10).json()[0]['batch']
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)

    return summary


@app.route("/respond", methods=["POST"])
def respond():
    start_time = time.time()
    dialog = request.json.get('dialog', [])

    logger.info(f"summarization-annotator received dialog: {dialog}")
    result = get_summary(dialog)

    total_time = time.time() - start_time
    logger.info(f"summarization-annotator exec time: {round(total_time, 2)} sec")
    logger.info(result)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8171)
