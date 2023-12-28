import logging
import os
import time
from typing import List, Dict

import sentry_sdk
from flask import Flask, request, jsonify
from nltk import sent_tokenize
from itertools import zip_longest

from models import get_speech_function

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


try:
    speech_function = get_speech_function("fine, thank you", "How are you doing?", "Open.Demand.Fact.")
    logger.info(speech_function)
    logger.info("model loaded, test query processed")
except Exception as e:
    logger.exception("model not loaded")
    sentry_sdk.capture_exception(e)
    raise e


def handler(payload: List[Dict]):
    responses = [""] * len(payload)
    try:
        for i, p in enumerate(payload):
            phrase_len = len(p["phrase"])
            phrases = [p["prev_phrase"]] + p["phrase"]
            authors = ["John"] + ["Doe"] * phrase_len
            response = [p["prev_speech_function"]]
            logger.info(f"PREV_SF:{response}")
            for phr, prev_phr, auth, prev_auth in zip(phrases[1:], phrases[:-1], authors[1:], authors[:-1]):
                speech_f = get_speech_function(phr, prev_phr, response[-1], auth, prev_auth)
                response.append(speech_f)
            responses[i] = response[1:]
            logger.info(f"RESPONSE:{response}")

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return responses


@app.route("/respond", methods=["POST"])  # annotation
def answer():
    st_time = time.time()
    phrases = request.json.get("phrase", [])
    prev_phrases = request.json.get("prev_phrase", [])
    prev_speech_funcs = request.json.get("prev_speech_function", [])
    payloads = []
    for phr, prev_phr, prev_speech_func in zip_longest(phrases, prev_phrases, prev_speech_funcs):
        payloads.append(
            {"phrase": sent_tokenize(phr), "prev_phrase": prev_phr, "prev_speech_function": prev_speech_func}
        )
    responses = handler(payloads)
    total_time = time.time() - st_time
    logger.info(f"speech_function_classifier model exec time: {total_time:.3f}s")
    return jsonify(responses)


@app.route("/respond_batch", methods=["POST"])  # candidate annotator
def annotation():
    st_time = time.time()
    phrases = request.json.get("phrase", [])
    prev_phrases = request.json.get("prev_phrase", [])
    prev_speech_funcs = request.json.get("prev_speech_function", [])
    payloads = []
    for phr, prev_phr, prev_speech_func in zip_longest(phrases, prev_phrases, prev_speech_funcs):
        payloads.append(
            {"phrase": sent_tokenize(phr), "prev_phrase": prev_phr, "prev_speech_function": prev_speech_func}
        )
    responses = handler(payloads)
    total_time = time.time() - st_time
    logger.info(f"speech_function_classifier batch exec time: {total_time:.3f}s")
    logger.info(f"speech function classifier result: {responses}")
    return [{"batch": responses}]
