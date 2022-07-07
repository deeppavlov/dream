import logging
import os
import sentry_sdk
import time
from flask import Flask, request, jsonify

from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

try:
    model = build_model("breakdown_config.json", download=True)
    test_res = model(["a"], ["b"])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


def get_result(contexts, curr_utterances):
    res = [{} for _ in curr_utterances]
    try:
        if contexts and curr_utterances:
            res = model(contexts, curr_utterances)
        else:
            raise Exception("Empty list of sentences received")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return res


@app.route("/model", methods=["POST"])
def respond():
    st_time = time.time()
    logger.info(request.json)
    contexts = request.json.get("context", [" "])
    curr_utterances = request.json.get("curr_utterance", [" "])
    answer = get_result(contexts, curr_utterances)

    total_time = time.time() - st_time
    logger.info(f"dialog breakdown exec time: {total_time:.3f}s")
    return jsonify(answer)


@app.route("/batch_model", methods=["POST"])
def batch_respond():
    st_time = time.time()
    logger.info(request.json)
    contexts = request.json.get("context", [" "])
    curr_utterances = request.json.get("curr_utterance", [" "])
    answer = get_result(contexts, curr_utterances)

    total_time = time.time() - st_time
    logger.info(f"dialog breakdown exec time: {total_time:.3f}s")
    return jsonify([{"batch": answer}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
