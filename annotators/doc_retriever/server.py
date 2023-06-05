import logging
import os
import sentry_sdk
import random
import string
import requests
import time
from deeppavlov import build_model
from urllib.parse import urlparse
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
FILE_SERVER_URL = os.environ.get("FILE_SERVER_URL", None)
server_url = urlparse(FILE_SERVER_URL)
assert CONFIG_PATH, logger.info("No config file name is given.")
assert DATASET_PATH, logger.info("No final dataset path is given.")
assert ORIGINAL_FILE_PATH, logger.info("No original file path is given.")
assert FILE_SERVER_URL, logger.info("No file server url path is given.")


def get_answers(utterance: str, ranker):
    ranker_output = ranker([utterance])
    raw_candidates = ranker_output[0]
    return raw_candidates


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def write_file_to_server(filename, filepath):
    resp = requests.post(FILE_SERVER_URL, files={"file": (filename, open(filepath, "rb"))}, timeout=30)
    resp.raise_for_status()
    download_link = resp.json()["downloadLink"]
    download_link = urlparse(download_link)._replace(scheme=server_url.scheme, netloc=server_url.netloc).geturl()
    return download_link


@app.route("/return_candidates", methods=["POST"])
def return_candidates():
    try:
        bot_attributes = request.json["dialogs"][-1].get("bot", {}).get("attributes", {})
        db_link = bot_attributes.get("db_path", "")
        matrix_link = bot_attributes.get("matrix_path", "")
        logger.info(f"Started downloading files from server (db_link: {db_link}, matrix_link: {matrix_link}).")
        db_file = requests.get(db_link)
        matrix_file = requests.get(matrix_link, timeout=30)
        if not os.path.exists("/data/odqa"):
            os.mkdir("/data/odqa")
        with open("/data/odqa/userfile.db", "wb") as f:
            f.write(db_file.content)
        with open("/data/odqa/userfile_tfidf_matrix.npz", "wb") as f:
            f.write(matrix_file.content)
        logger.info("Files downloaded successfully.")
        ranker_model = build_model(CONFIG_PATH)
        logger.info("Model loaded.")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        raise e
    utterances = request.json["dialogs"][-1]["utterances"][-1]["text"]
    results = get_answers(utterances, ranker_model)
    logger.info(f"Output candidate files: '{str(results)}'.")
    return jsonify(
        [
            {
                "candidate_files": results,
                "dataset_path": DATASET_PATH,
                "file_path": ORIGINAL_FILE_PATH,
            }
        ]
    )


@app.route("/save_model_path", methods=["POST"])
def save_model_path():
    logger.info("Started writing files to server.")
    bot_attributes = request.json["dialogs"][-1].get("bot", {}).get("attributes", {})
    if "db_path" not in bot_attributes:
        file_name = generate_random_string(10)
        db_file_name = f"{file_name}.db"
        matrix_file_name = f"{file_name}.npz"
        try:
            db_link = write_file_to_server(db_file_name, "/data/odqa/userfile.db")
            matrix_link = write_file_to_server(matrix_file_name, "/data/odqa/userfile_tfidf_matrix.npz")
            time.sleep(1)
            os.remove("/data/odqa/userfile.db")
            os.remove("/data/odqa/userfile_tfidf_matrix.npz")
            logger.info("Files successfully written to server and removed from /data.")
            result = [{"bot_attributes": {"db_path": db_link, "matrix_path": matrix_link}}]
            logger.info(f"Bot attributes in save_model: {result}")
        except Exception as e:
            logger.error(e)
    else:
        result = [{}]
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
