import logging
import time
import os

import sentry_sdk
from catboost import CatBoostClassifier
from flask import Flask, request, jsonify
from score import get_features

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def get_probas(contexts, hypotheses):
    features = get_features(contexts, hypotheses)
    pred = cb.predict_proba(features)[:, 1]
    return pred


try:
    cb = CatBoostClassifier()
    cb.load_model("model.cbm")
except Exception as e:
    logger.exception("Scorer not loaded")
    sentry_sdk.capture_exception(e)
    raise e


@app.route("/batch_model", methods=["POST"])
def batch_respond():
    st_time = time.time()
    contexts = request.json["contexts"]
    hypotheses = request.json["hypotheses"]

    try:
        responses = get_probas(contexts, hypotheses).tolist()
    except Exception as e:
        responses = [0] * len(hypotheses)
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    logging.info(f"hypothesis_scorer exec time {time.time() - st_time}")
    return jsonify([{"batch": responses}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
