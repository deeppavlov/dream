import logging
import os
import time

from flask import Flask, request, jsonify
import sentry_sdk

from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

try:
    model = build_model("combined_cobot_classifier.json", download=False)
    test_res = model(["a"], ['b'])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


def get_result(histories, phrases):
    st_time = time.time()
    res = [{} for _ in phrases]
    if not phrases:
        phrases = [" "]
    if not histories:
        histories = []  # or [" "]
    try:
        if phrases:
            res = model(histories, phrases)
        else:
            raise Exception("Empty list of sentences received")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    total_time = time.time() - st_time
    logger.info(f'combined_cobot_classifier exec time: {total_time:.3f}s')
    return res


@app.route("/model", methods=["POST"])
def respond():
    logger.info(request.json)
    phrases = request.json.get("phrase", [" "])
    histories = request.json.get("history", [" "])
    answer = get_result(histories, phrases)
    return jsonify(answer)


@app.route("/batch_model", methods=["POST"])
def batch_respond():
    logger.info(request.json)
    phrases = request.json.get("phrase", [" "])
    histories = request.json.get("history", [" "])
    answer = get_result(histories, phrases)
    return jsonify([{"batch": answer}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
