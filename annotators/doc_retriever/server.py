import logging
import os
from pathlib import PurePath

import requests
import sentry_sdk
from common.files_and_folders_processing import create_folders_if_not_exist
from deeppavlov import build_model
from deeppavlov.core.common.file import read_json
from flask import Flask, jsonify, request
from healthcheck import HealthCheck
from sentry_sdk.integrations.flask import FlaskIntegration
from utils import vectorize_upload_return_attributes, download_files, add_file_id_to_config

# logging here because it conflicts with tf

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")

PARAGRAPHS_NUM = int(os.environ.get("PARAGRAPHS_NUM", 5))
FILE_SERVER_TIMEOUT = float(os.environ.get("FILE_SERVER_TIMEOUT", 30))
CONFIG_PATH = os.environ.get("CONFIG_PATH", None)
SERVICE_PORT = os.environ.get("SERVICE_PORT", None)
FILE_SERVER_URL = os.environ.get("FILE_SERVER_URL", None)
assert FILE_SERVER_URL, logger.error("Error: FILE_SERVER_URL is not specified in env")
MODEL_CONFIG = read_json(CONFIG_PATH)
MODEL_CONFIG["dataset_reader"]["dataset_format"] = "txt"
MODEL_CONFIG["chainer"]["pipe"][1]["top_n"] = PARAGRAPHS_NUM


@app.route("/vectorize_documents", methods=["POST"])
def vectorize_documents():
    attributes_to_add = []
    dialogs = request.json["dialogs"]
    create_folders_if_not_exist(["/data/documents", "/data/odqa"])
    for dialog in dialogs:
        filepaths_in_container, files_to_vectorize = [], []
        documents_in_use = dialog.get("human", {}).get("attributes", {}).get("documents_in_use", {})
        dialog_id = dialog["dialog_id"]
        if documents_in_use:  # vectorize documents if there are any documents_in_use
            try:
                for file_id in documents_in_use.keys():  # get links to all files that are not vectorized
                    is_vectorised = documents_in_use[file_id].get("vectors_processed", False)
                    if not is_vectorised:
                        document_link = documents_in_use[file_id].get("full_processed_text_link", "")
                        if document_link not in files_to_vectorize:
                            files_to_vectorize.append(document_link)
                if files_to_vectorize:  # vectorize files that are not vectorized if any
                    filepaths_in_container = download_files(files_to_vectorize, filepaths_in_container)
                    model_config = add_file_id_to_config(MODEL_CONFIG, file_id)
                    model_info, documents_in_use = vectorize_upload_return_attributes(
                        model_config, filepaths_in_container, documents_in_use, dialog_id
                    )
                    bot_and_human_atts = {
                        "bot_attributes": {"model_info": {file_id: model_info}},
                        "human_attributes": {"documents_in_use": documents_in_use},
                    }
                    attributes_to_add.append(bot_and_human_atts)
                else:
                    logger.info("All files are already vectorized. Skipping vectorization.")
                    attributes_to_add.append({})
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)
                attributes_to_add.append({})
        else:
            logger.info("No documents in use found.")
            attributes_to_add.append({})
    return jsonify(attributes_to_add)


@app.route("/return_candidates", methods=["POST"])
def return_candidates():
    candidates_list = []
    dialogs = request.json["dialogs"]
    for dialog in dialogs:
        create_folders_if_not_exist(["/data/documents", "/data/odqa"])
        curr_docs = list(dialog.get("human", {}).get("attributes", {}).get("documents_in_use", {}).keys())
        if curr_docs:
            # now we always have one file in use (concatenated texts from several inputs) so taking first and only key
            curr_doc = curr_docs[0]
            model_info = dialog.get("bot", {}).get("attributes", {}).get("model_info", {})
            # get vectorization results for our specific file in use
            db_link = model_info.get(curr_doc, {}).get("db_link", "")
            matrix_link = model_info.get(curr_doc, {}).get("matrix_link", "")
            if db_link and matrix_link:
                try:
                    # ensure unique file names by adding ids, dblink format: "{FILE_SERVER_URL}/file?file={FILE_ID}.db"
                    file_id = PurePath(db_link.split("=")[-1]).stem
                    tfidf_matrix_path = f"/data/odqa/userfile_tfidf_matrix_{file_id}.npz"
                    userfile_path = f"/data/odqa/userfile_{file_id}.db"
                    if os.path.isfile(tfidf_matrix_path) and os.path.isfile(
                        userfile_path
                    ):  # check if we already have model files in container
                        logger.info(
                            f"{userfile_path} and {tfidf_matrix_path} are already in container, skipping downloading."
                        )
                    else:  # if no, download model files from server
                        logger.info(
                            f"""Downloading {db_link} to {userfile_path}, {matrix_link} to {tfidf_matrix_path})."""
                        )
                        db_file = requests.get(db_link, timeout=FILE_SERVER_TIMEOUT)
                        matrix_file = requests.get(matrix_link, timeout=FILE_SERVER_TIMEOUT)
                        with open(userfile_path, "wb") as f:
                            f.write(db_file.content)
                        with open(tfidf_matrix_path, "wb") as f:
                            f.write(matrix_file.content)
                        logger.info("Files downloaded successfully.")
                    # adding our files' ids to model's config to ensure that we build it from the files we need
                    model_config = add_file_id_to_config(MODEL_CONFIG, file_id)
                    ranker_model = build_model(model_config)
                    logger.info("Model loaded.")
                    last_human_utterance = dialog.get("human_utterances", [{}])[-1].get("text", "")
                    # get candidates that are closest to last user utterance
                    # ranker_model([x]) processes batches and outputs [[result]], thus we take item [0]
                    results = ranker_model([last_human_utterance])[0]
                    candidates_list.append({"candidate_files": results})
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    logger.exception(e)
                    candidates_list.append({})
                logger.info(f"Output candidate files: '{candidates_list}'.")
            else:
                logger.info(
                    "There are documents in use but they were not vectorized. \
Check if doc-retriever /vectorize_documents endpoint works correctly."
                )
                candidates_list.append({})
        else:
            logger.info("No documents in use found.")
            candidates_list.append({})
    return jsonify(candidates_list)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
