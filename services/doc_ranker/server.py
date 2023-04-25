import logging
import os
from typing import List
import sentry_sdk
from deeppavlov import build_model
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration

# logging here because it conflicts with tf
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)
DATASET_PATH = os.environ.get("DATASET_PATH", None)
ORIGINAL_FILE_PATH = os.environ.get("ORIGINAL_FILE_PATH", None)
CONFIG_PATH = os.environ.get("CONFIG_PATH", None)
SERVICE_PORT = os.environ.get("SERVICE_PORT", None)
if CONFIG_PATH is None:
    raise NotImplementedError("No config file name is given.")
if DATASET_PATH is None:
    raise NotImplementedError("No final dataset path is given.")
if ORIGINAL_FILE_PATH is None:
    raise NotImplementedError("No original file path is given.")


try:
    ranker_model = build_model(CONFIG_PATH)
    logger.info("Model loaded")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


def get_answers(utterance: str, ranker):
    ranker_output = ranker(utterance)[0]
    candidates = []
    nums = 0
    for f_name in ranker_output:
        nums += 1
        with open(DATASET_PATH + f_name) as f:
            candidates.append(f"{nums}. {f.read()}")
    return " ".join(candidates)


@app.route("/rank", methods=["POST"])
def detect():
    utterances = request.json["sentences"][-1]
    logger.info(f"Input: `{utterances}`.")
    results = get_answers(utterances, ranker_model)
    logger.info(f"Output: `{results}`.")
    return jsonify(results)
