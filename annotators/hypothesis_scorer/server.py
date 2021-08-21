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
logging.getLogger("werkzeug").setLevel("WARNING")

app = Flask(__name__)


def get_probas(contexts, hypotheses):
    features = get_features(contexts, hypotheses)
    pred = cb.predict_proba(features)[:, 1]
    return pred


try:
    cb = CatBoostClassifier()
    cb.load_model("model-confidence-convert-old_midas.cbm")
    contexts = [[
        "i'm good how are you",
        "Spectacular, by all reports! Do you want to know what I can do?",
        "absolutely",
        "I'm a socialbot running inside Alexa, and I'm all about chatting with people like you. "
        "I can answer questions, share fun facts, discuss movies, books and news. What do you want to talk about?",
        "let's talk about movies"
    ]]
    hypotheses = [{
        "is_best": True,
        "text": "Kong: Skull Island is a good action movie. What do you think about it?",
        "confidence": 1.0,
        "cobot_convers_evaluator_annotator": {
            "isResponseOnTopic": 0.505,
            "isResponseErroneous": 0.938,
            "responseEngagesUser": 0.344,
            "isResponseInteresting": 0.084,
            "isResponseComprehensible": 0.454
        }
    }]
    get_probas(contexts, hypotheses)
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

    logging.warning(f"hypothesis_scorer exec time {time.time() - st_time}")
    return jsonify([{"batch": responses}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
