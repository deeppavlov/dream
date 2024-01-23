from typing import List
import logging
import os
import time

import sentry_sdk
from flask import Flask, request, jsonify

from model import init_model

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


class_dict, counters, label_to_name = init_model()


def predict(label_name):
    try:
        class_id = class_dict[label_name]
    except KeyError:
        return {}
    sorted_classes = sorted(enumerate(counters[class_id]), reverse=True, key=lambda x: x[1])
    sorted_classes = [x for x in sorted_classes if x[1] > 0]
    return [{"prediction": label_to_name[label], "confidence": probability} for label, probability in sorted_classes]


try:
    predict("Reply.Acknowledge")
    logger.info("model loaded, test query processed")
except Exception as e:
    logger.exception("model not loaded")
    sentry_sdk.capture_exception(e)
    raise e


def handler(payload: List[str]):
    responses = [{}] * len(payload)
    try:
        responses = [predict(speech_function) for speech_function in payload]
        logger.info(f"PREDICTED SCORE FOR SPEECH FUNC: {responses}")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return responses


@app.route("/respond", methods=["POST"])
def answer():
    st_time = time.time()
    payload = request.json.get("funcs", [])
    responses = handler(payload)
    total_time = time.time() - st_time
    logger.info(f"sfp RESULT: {responses}")
    logger.info(f"speech_function_predictor model exec time: {total_time:.3f}s")
    return jsonify(responses)


@app.route("/respond_batch", methods=["POST"])  # /annotation & /model -> /respond_batch & /respond
def annotation():
    st_time = time.time()
    payload = request.json.get("funcs", [])
    logger.info(f"PAYLOAD IN BATCH RESPOND SFP --------------------------------: {payload}")
    responses = handler(payload)
    total_time = time.time() - st_time
    logger.info(f"speech_function_predictor batch exec time: {total_time:.3f}s")
    return [{"batch": responses}]
