import logging
import os
from typing import List

import sentry_sdk
from deeppavlov import build_model
from deeppavlov.core.commands.utils import parse_config, expand_path
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from utils import get_regexp

# logging here because it conflicts with tf
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)


INTENT_PHRASES_PATH = os.environ.get("INTENT_PHRASES_PATH", "intent_phrases.json")
CONFIG_NAME = os.environ.get("CONFIG_NAME", None)
if CONFIG_NAME is None:
    raise NotImplementedError("No config file name is given.")
parsed = parse_config(CONFIG_NAME)
with open(expand_path(parsed["metadata"]["variables"]["MODEL_PATH"]).joinpath("classes.dict"), "r") as f:
    intents = f.read().strip().splitlines()
intents = [el.strip() for el in intents]
logger.info(f"Considered intents: {intents}")

try:
    intents_model = build_model(CONFIG_NAME, download=True)
    logger.info("Model loaded")
    regexp = get_regexp(INTENT_PHRASES_PATH)
    logger.info("Regexp model loaded")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


def predict_intents(batch_texts: List[str], intents, regexp):
    result = []
    # classify with intent catcher neural model
    pred_labels, pred_probas = intents_model(batch_texts)

    for text_id, text in enumerate(batch_texts):
        resp = {intent: {"detected": 0, "confidence": 0.0} for intent in intents}
        for intent, regs in regexp.items():
            for i, utt in enumerate(text):
                for reg in regs:
                    if reg.fullmatch(utt):
                        resp[intent]["detected"] = 1
                        resp[intent]["confidence"] = 1.0
                        break
        resp = {
            intent: resp[intent]
            if resp[intent]["detected"]
            else {"detected": int(float(proba) > 0.5), "confidence": float(proba)}
            for intent, proba in zip(intents, pred_probas[text_id])
        }
        result += resp

    return result


@app.route("/detect", methods=["POST"])
def detect():
    utterances = request.json["sentences"]
    utterances = [" ".join(uttr) if isinstance(uttr, list) else uttr for uttr in utterances]
    logger.info(f"Input to classify: `{utterances}`.")
    results = predict_intents(utterances, intents, regexp)

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8014)
