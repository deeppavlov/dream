import logging
import os

import sentry_sdk
import torch
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, EvalPrediction
from utils import create_label_map

# logging here because it conflicts with tf
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

app = Flask(__name__)

INTENTS_MODEL_PATH = os.environ.get("INTENTS_MODEL_PATH", None)
TRANSFORMERS_MODEL_PATH = os.environ.get("TRANSFORMERS_MODEL_PATH", None)
if TRANSFORMERS_MODEL_PATH is None:
    TRANSFORMERS_MODEL_PATH = "sentence-transformers/distiluse-base-multilingual-cased-v2"

try:
    tokenizer = AutoTokenizer.from_pretrained(TRANSFORMERS_MODEL_PATH)
    logger.info("Tokenizer loaded")

    with open("intents.txt", "r") as f:
        intents = f.readlines()
        intents = [intent for intent in intents if intent]
    id2label, label2id = create_label_map(intents)
    logger.info("Intents map loaded")

    classification_model = AutoModelForSequenceClassification.from_pretrained(
        INTENTS_MODEL_PATH,
        num_labels=len(intents),
        problem_type="multi_label_classification",
        id2label=id2label,
        label2id=label2id
    )
    logger.info("Intents model loaded")

except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


def predict_intents(text):
    global tokenizer, classification_model, intents
    encoding = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        outputs = classification_model(**encoding)
        predictions = torch.sigmoid(outputs.logits).numpy()

    return {intent: {"detected": int(float(proba) > 0.5), "confidence": float(proba)}
            for intent, proba in zip(intents, predictions)}


@app.route("/detect", methods=["POST"])
def detect():
    utterances = request.json["sentences"]
    logger.info(f"Number of utterances: {len(utterances)}")
    results = []
    for uttr in utterances:
        results += [predict_intents(uttr)]

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8014)

