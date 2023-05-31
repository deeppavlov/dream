import logging
import os
import sentry_sdk
import random
import string
import requests
from deeppavlov import build_model
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration

# logging here because it conflicts with tf
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)
DATASET_PATH = os.environ.get("DATASET_PATH", None)
ORIGINAL_FILE_PATH = os.environ.get("ORIGINAL_FILE_PATH", None)
CONFIG_PATH = os.environ.get("CONFIG_PATH", None)
SERVICE_PORT = os.environ.get("SERVICE_PORT", None)
FILE_SERVER_URL = os.environ.get("SERVICE_PORT", None)
assert CONFIG_PATH, logger.info("No config file name is given.")
assert DATASET_PATH, logger.info("No final dataset path is given.")
assert ORIGINAL_FILE_PATH, logger.info("No original file path is given.")
assert FILE_SERVER_URL, logger.info("No file server url path is given.")


try:
    ranker_model = build_model(CONFIG_PATH)
    logger.info("Model loaded")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


def get_answers(utterance: str, ranker):
    ranker_output = ranker(utterance)
    logger.info(f"ranker_output: `{ranker_output}`")
    raw_candidates = ranker_output[0]
    num_candidates = []
    nums = 0
    for f_name in raw_candidates:
        nums += 1
        with open(DATASET_PATH + f_name) as f:
            num_candidates.append(f"{nums}. {f.read()}")
    return " ".join(num_candidates)


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def write_file_to_server(filename, filepath):
    resp = requests.post(
        FILE_SERVER_URL, files={"file": (filename, open(filepath, "rb"))}
    )
    resp.raise_for_status()


@app.route("/return_candidates", methods=["POST"])
def return_candidates():
    utterances = request.json["sentences"][-1]
    logger.info(f"Input: `{utterances}`.")
    results = get_answers(utterances, ranker_model)
    logger.info(f"Output: `{results}`.")
    return jsonify(results)


@app.route("/save_model_path", methods=["POST"])
def save_model_path():
    file_name = generate_random_string(10)
    db_file_name = f"{file_name}.db"
    matrix_file_name = f"{file_name}.npz"
    try:
        resp_db = write_file_to_server(db_file_name, "/data/odqa/userfile.db")
        resp_mat = write_file_to_server(matrix_file_name, "/data/odqa/userfile_tfidf_matrix.npz")
        result = [
        {"bot_attribiutes": {"db_path": matrix_file_name, "matrix_path": db_file_name}}
    ]
    except Exception as e:
        logger.error(e)
    return jsonify(result)
