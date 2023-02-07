"""
Source code is https://github.com/Grossmend/DialoGPT/blob/master/src/service/service.py
"""
import logging
import time
import os

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from healthcheck import HealthCheck
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import BertTokenizer, BertForSequenceClassification


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH", "s-nlp/russian_toxicity_classifier")
logger.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")

cuda = torch.cuda.is_available()
if cuda:
    torch.cuda.set_device(0)
    device = "cuda"
else:
    device = "cpu"

logger.info(f"toxic-classification is set to run on {device}")

try:
    tokenizer = BertTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = BertForSequenceClassification.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model.eval()
    if cuda:
        model.cuda()
    logger.info("toxic-classification model is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")
logging.getLogger("werkzeug").setLevel("WARNING")


def classify_sentences(sentences):
    try:
        batch_tokens = []
        for sent in sentences:
            batch_tokens += [tokenizer.encode(sent, padding="max_length", max_length=64, return_tensors="pt")]

        model_input = torch.cat(batch_tokens, dim=0)
        model_input = model_input.cuda() if cuda else model_input
        result = []
        with torch.no_grad():
            outputs = model(model_input)
            probas = torch.nn.functional.softmax(outputs.logits, dim=-1)
            for sent, prob_dist in zip(sentences, probas):
                result += [{"toxic": float(prob_dist[1])}]
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        result = [{"toxic": 0.0}] * len(sentences)
    return result


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    sentences = request.json.get("sentences", [])
    result = classify_sentences(sentences)
    total_time = time.time() - st_time
    logger.info(f"toxic-classification exec time: {total_time:.3f}s")

    return jsonify(result)


@app.route("/respond_batch", methods=["POST"])
def respond_batch():
    st_time = time.time()
    sentences = request.json.get("sentences", [])
    result = classify_sentences(sentences)
    total_time = time.time() - st_time
    logger.info(f"toxic-classification exec time: {total_time:.3f}s")

    return jsonify([{"batch": result}])
