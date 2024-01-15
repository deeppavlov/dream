import logging
import os
import time

import sentry_sdk
from flask import Flask, request, jsonify
from models import get_speech_functions

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


try:
    speech_function = get_speech_functions(
        ["fine, thank you"],
        ["How are you doing?"],
        ["Open.Demand.Fact."],
        speakers=["John"],
        previous_speakers=["Doe"],
    )
    logger.info(speech_function)
    logger.info("model loaded, test query processed")
except Exception as e:
    logger.exception("model not loaded")
    sentry_sdk.capture_exception(e)
    raise e


@app.route("/respond", methods=["POST"])  # annotation
def answer():
    st_time = time.time()
    phrases = request.json.get("phrases", [])
    prev_phrases = request.json.get("prev_phrases", None)
    prev_phrases = ["" for _ in phrases] if prev_phrases is None else prev_phrases
    prev_speech_funcs = request.json.get("prev_speech_functions", None)
    prev_speech_funcs = ["" for _ in phrases] if prev_speech_funcs is None else prev_speech_funcs

    responses = get_speech_functions(phrases, prev_phrases, prev_speech_funcs)
    logger.info(f"speech_function_classifier responses: {responses}")

    total_time = time.time() - st_time
    logger.info(f"speech_function_classifier model exec time: {total_time:.3f}s")
    return jsonify(responses)


@app.route("/respond_batch", methods=["POST"])  # candidate annotator
def annotation():
    st_time = time.time()
    phrases = request.json.get("phrases", [])
    prev_phrases = request.json.get("prev_phrases", None)
    prev_phrases = ["" for _ in phrases] if prev_phrases is None else prev_phrases
    prev_speech_funcs = request.json.get("prev_speech_functions", None)
    prev_speech_funcs = ["" for _ in phrases] if prev_speech_funcs is None else prev_speech_funcs

    responses = get_speech_functions(phrases, prev_phrases, prev_speech_funcs)
    logger.info(f"speech_function_classifier responses: {responses}")

    total_time = time.time() - st_time
    logger.info(f"speech_function_classifier batch exec time: {total_time:.3f}s")
    logger.info(f"speech function classifier result: {responses}")
    return [{"batch": responses}]
