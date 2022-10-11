import logging
import time
import os

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import XLMRobertaForSequenceClassification, XLMRobertaTokenizer

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
logging.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
columns = ["negative", "neutral", "positive"]

try:
    tokenizer = XLMRobertaTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = XLMRobertaForSequenceClassification.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model.eval()
    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("sentiment-classification is set to run on cuda")

    logger.info("sentiment-classification model is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def classify_sentences(sentences):
    try:
        inputs = tokenizer(sentences, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            if torch.cuda.is_available():
                inputs = inputs.to("cuda")
            outputs = model(**inputs)[0]
            model_output = torch.nn.functional.softmax(outputs, dim=-1).cpu()
            result = []

            for i, cla in zip(sentences, model_output):
                result += [{columns[id_column]: float(cla[id_column]) for id_column in range(len(columns))}]

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        result = [{column: 0.0 for column in columns}] * len(sentences)
    return result


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    sentences = request.json.get("sentences", [])
    result = classify_sentences(sentences)
    total_time = time.time() - st_time
    logger.info(f"sentiment-classification exec time: {total_time:.3f}s")

    return jsonify(result)


@app.route("/respond_batch", methods=["POST"])
def respond_batch():
    st_time = time.time()
    sentences = request.json.get("sentences", [])
    result = classify_sentences(sentences)
    total_time = time.time() - st_time
    logger.info(f"sentiment-classification exec time: {total_time:.3f}s")

    return jsonify([{"batch": result}])
