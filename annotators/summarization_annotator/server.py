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

SUMMARIZATION_REQUEST_TIMEOUT = float(getenv("SUMMARIZATION_REQUEST_TIMEOUT"))
SUMMARIZATION_SERVICE_URL = getenv("SUMMARIZATION_SERVICE_URL")
logger.info(f"summarization-annotator considered summarizer: {SUMMARIZATION_SERVICE_URL}")


def get_summary(dialog):
    summary = ""
    if len(dialog) != 11:
        logger.debug(
            f"summarization-annotator is not ready to summarize dialog as the length of unsummarized dialog is "
            f"{len(dialog)} != 11"
        )
        return summary

    logger.debug("summarization-annotator is ready to summarize dialog as the length of unsummarized dialog is 11")
    dialog = dialog[:6]
    for i in range(len(dialog)):
        if i % 2 == 0:
            dialog[i] = "User: " + dialog[i]
        else:
            dialog[i] = "Bot: " + dialog[i]
    dialog = ["\n".join(dialog)]
    logger.debug(f"summarization-annotator will summarize this: {dialog}")

    try:
        summary = requests.post(
            SUMMARIZATION_SERVICE_URL,
            json={"sentences": dialog},
            timeout=SUMMARIZATION_REQUEST_TIMEOUT,
        ).json()[0]["batch"][0]
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)

    return summary


@app.route("/respond", methods=["POST"])
def respond():
    start_time = time.time()
    dialogs_batch = request.json.get("dialogs", [])
    summaries_batch = request.json.get("previous_summaries", [])
    summarization_attribute = []

    for dialog, prev_summary in zip(dialogs_batch, summaries_batch):
        logger.debug(f"summarization-annotator received dialog: {dialog}")
        logger.debug(f"summarization-annotator received previous summary: {[prev_summary]}")
        result = prev_summary
        new_summary = get_summary(dialog)
        if new_summary:
            result = f"{result} {new_summary}".strip()
        summarization_attribute.append({"bot_attributes": {"summarized_dialog": result}})
        logger.info(f"summarization-annotator output: {summarization_attribute}")

    total_time = time.time() - start_time
    logger.info(f"summarization-annotator exec time: {total_time:.2f}s")
    return jsonify(summarization_attribute)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8058)
