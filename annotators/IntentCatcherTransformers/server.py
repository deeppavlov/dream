import json
import logging
import os
from itertools import chain
from typing import List

import numpy as np
import sentry_sdk
from deeppavlov import build_model
from deeppavlov.core.commands.utils import parse_config, expand_path
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from utils import get_regexp, unite_responses

# logging here because it conflicts with tf
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)


INTENT_PHRASES_PATH = os.environ.get("INTENT_PHRASES_PATH", "intent_phrases.json")
CONFIG_NAME = os.environ.get("CONFIG_NAME", None)
if CONFIG_NAME is None:
    raise NotImplementedError("No config file name is given.")

try:
    intents_model = build_model(CONFIG_NAME, download=True)
    logger.info("Model loaded")
    regexp = get_regexp(INTENT_PHRASES_PATH)
    logger.info("Regexp model loaded")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

parsed = parse_config(CONFIG_NAME)
with open(expand_path(parsed["metadata"]["variables"]["MODEL_PATH"]).joinpath("classes.dict"), "r") as f:
    intents = f.read().strip().splitlines()
CLS_INTENTS = [el.strip().split("\t")[0] for el in intents]
ALL_INTENTS = list(json.load(open(INTENT_PHRASES_PATH))["intent_phrases"].keys())
logger.info(f"Considered intents for classifier: {CLS_INTENTS}")
logger.info(f"Considered intents from json file: {ALL_INTENTS}")


def get_classifier_predictions(batch_texts: List[List[str]], intents_model, thresholds):
    global CLS_INTENTS
    if thresholds is None:
        # if we do not given thresholds, use 0.5 as default
        thresholds = [0.5] * len(CLS_INTENTS)
    thresholds = np.array(thresholds)
    # make a 1d-list of texts for classifier
    sentences = list(chain.from_iterable(batch_texts))
    sentences_text_ids = []
    for text_id, text in enumerate(batch_texts):
        sentences_text_ids += [text_id] * len(text)
    sentences_text_ids = np.array(sentences_text_ids)

    result = []
    # classify with intent catcher classifier
    if len(sentences) > 0:
        _, pred_probas = intents_model(sentences)
        for text_id, text in enumerate(batch_texts):
            maximized_probas = np.max(pred_probas[sentences_text_ids == text_id], axis=0)
            resp = {
                intent: {"detected": int(float(proba) > thresh), "confidence": round(float(proba), 3)}
                for intent, thresh, proba in zip(CLS_INTENTS, thresholds, maximized_probas)
            }
            result += [resp]
    return result


def predict_intents(batch_texts: List[List[str]], regexp, intents_model, thresholds=None):
    global ALL_INTENTS
    responds = []
    not_detected_utterances = []
    for text_id, text in enumerate(batch_texts):

        resp = {intent: {"detected": 0, "confidence": 0.0} for intent in ALL_INTENTS}
        not_detected_utterance = text.copy()
        for intent, reg in regexp.items():
            for i, utt in enumerate(text):
                if reg.fullmatch(utt):
                    logger.info(f"Full match of `{utt}` with `{reg}`.")
                    resp[intent]["detected"] = 1
                    resp[intent]["confidence"] = 1.0
                    not_detected_utterance[i] = None
        not_detected_utterance = [utt for utt in not_detected_utterance if utt]
        not_detected_utterances.append(not_detected_utterance)
        responds.append(resp)

    if len(not_detected_utterances) > 0 and len(not_detected_utterances[0]) > 0:
        classifier_result = get_classifier_predictions(not_detected_utterances, intents_model, thresholds)
        return unite_responses(classifier_result, responds, ALL_INTENTS)
    else:
        return responds


@app.route("/detect", methods=["POST"])
def detect():
    utterances = request.json["sentences"]
    logger.info(f"Input: `{utterances}`.")
    results = predict_intents(utterances, regexp, intents_model)
    logger.info(f"Output: `{results}`.")
    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8014)
