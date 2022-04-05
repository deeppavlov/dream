import logging
import os
from typing import List

import sentry_sdk
import torch
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from utils import create_label_map, get_regexp

# logging here because it conflicts with tf
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

app = Flask(__name__)

INTENT_PHRASES_PATH = os.environ.get("INTENT_PHRASES_PATH", "intent_phrases.json")
INTENTS_MODEL_PATH = os.environ.get("INTENTS_MODEL_PATH", "intent_model_v0")
TRANSFORMERS_MODEL_PATH = os.environ.get("TRANSFORMERS_MODEL_PATH", None)


try:
    tokenizer = AutoTokenizer.from_pretrained(TRANSFORMERS_MODEL_PATH)
    logger.info("Tokenizer loaded")

    regexp = get_regexp(INTENT_PHRASES_PATH)

    with open(f"/data/{INTENTS_MODEL_PATH}/intents.txt", "r") as f:
        intents = f.read().splitlines()
        intents = [intent.strip() for intent in intents if intent]
    id2label, label2id = create_label_map(intents)
    logger.info(f"Intents map loaded: {intents}")

    classification_model = AutoModelForSequenceClassification.from_pretrained(
        f"/data/{INTENTS_MODEL_PATH}",
        num_labels=len(intents),
        problem_type="multi_label_classification",
        id2label=id2label,
        label2id=label2id,
    )
    if torch.cuda.is_available():
        classification_model.to("cuda")
        logger.info("Intents model set on cuda")
    classification_model.eval()
    logger.info("Intents model loaded")

except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


def predict_intents(text: List[str]):
    global tokenizer, classification_model, intents, regexp
    encoding = tokenizer(" ".join(text), return_tensors="pt")
    resp = {intent: {"detected": 0, "confidence": 0.0} for intent in intents}

    for intent, regs in regexp.items():
        for i, utt in enumerate(text):
            for reg in regs:
                if reg.fullmatch(utt):
                    resp[intent]["detected"] = 1
                    resp[intent]["confidence"] = 1.0
                    break
    with torch.no_grad():
        if torch.cuda.is_available():
            encoding.to("cuda")
        outputs = classification_model(**encoding)
        predictions = torch.sigmoid(outputs.logits)
        if torch.cuda.is_available():
            predictions = predictions.cpu()
        predictions = predictions.numpy()[0]

    resp = {
        intent: resp[intent]
        if resp[intent]["detected"]
        else {"detected": int(float(proba) > 0.5), "confidence": float(proba)}
        for intent, proba in zip(intents, predictions)
    }
    return resp


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
