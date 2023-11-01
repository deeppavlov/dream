import logging
import os
import sentry_sdk
import requests
from pathlib import PurePath
from deeppavlov import build_model
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov.core.common.file import read_json
from utils import vectorize_upload_return_attributes, download_files, add_file_id_to_config
from common.files_and_folders_processing import create_folders_if_not_exist, generate_unique_file_id

# logging here because it conflicts with tf

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)

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
        docs_in_use = dialog.get("human", {}).get("attributes", {}).get("documents_in_use", [])
        processed_documents = dialog.get("human", {}).get("attributes", {}).get("processed_documents", {})
        model_info = dialog.get("human", {}).get("attributes", {}).get("model_info", {})
        docs_in_model = model_info.get("file_ids", [])
        dialog_id = dialog.get("dialog_id", "")
        # vectorize documents if there are any docs_in_use
        # and if the current model does not feature these docs_in_use
        if docs_in_use and docs_in_use != docs_in_model:
            try:
                for file_id in docs_in_use:
                    document_link = processed_documents[file_id].get("processed_text_link", "")
                    if document_link not in files_to_vectorize:
                        files_to_vectorize.append(document_link)
                # vectorize files that are not vectorized if any
                if files_to_vectorize:
                    # download files to container
                    filepaths_in_container = download_files(files_to_vectorize, filepaths_in_container)
                    # model id = random id that will be used in model filenames
                    model_id = generate_unique_file_id(10, dialog_id)
                    model_config = add_file_id_to_config(MODEL_CONFIG, model_id)
                    # build model and vectorize filepaths_in_container (downloaded on previous step)
                    model_info = vectorize_upload_return_attributes(
                        model_config, filepaths_in_container, docs_in_use, model_id
                    )
                    human_atts = {"human_attributes": {"model_info": model_info}}
                    attributes_to_add.append(human_atts)
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
        docs_in_use = dialog.get("human", {}).get("attributes", {}).get("documents_in_use", [])
        if docs_in_use:
            model_info = dialog.get("human", {}).get("attributes", {}).get("model_info", {})
            # get vectorization results for our specific file in use
            db_link = model_info.get("db_link", "")
            matrix_link = model_info.get("matrix_link", "")
            if db_link and matrix_link:
                try:
                    # ensure unique file names by adding ids
                    # dblink format: "{FILE_SERVER_URL}/file?file={MODEL_ID}.db"
                    model_id = PurePath(db_link.split("=")[-1]).stem
                    tfidf_matrix_path = f"/data/odqa/userfile_tfidf_matrix_{model_id}.npz"
                    userfile_path = f"/data/odqa/userfile_{model_id}.db"
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
                    model_config = add_file_id_to_config(MODEL_CONFIG, model_id)
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
