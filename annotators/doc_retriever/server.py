import logging
import os
import sentry_sdk
import requests
from deeppavlov import build_model
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov.core.common.file import read_json
from utils import (
    create_folders_if_not_exist,
    find_and_download_docs_if_needed,
    download_files_and_save_links,
    move_files_and_save_paths,
    train_upload_return_attributes,
    remove_files_and_folders,
)

# logging here because it conflicts with tf

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)

PARAGRAPHS_NUM = int(os.environ.get("PARAGRAPHS_NUM", 5))
FILE_SERVER_TIMEOUT = float(os.environ.get("FILE_SERVER_TIMEOUT", 30))
DOC_PATH_OR_LINK = os.environ.get("DOC_PATH_OR_LINK", "")
if DOC_PATH_OR_LINK and not isinstance(DOC_PATH_OR_LINK, list):
    DOC_PATH_OR_LINK = DOC_PATH_OR_LINK.split(",")  # we may have multiple files
CONFIG_PATH = os.environ.get("CONFIG_PATH", None)
SERVICE_PORT = os.environ.get("SERVICE_PORT", None)
FILE_SERVER_URL = os.environ.get("FILE_SERVER_URL", None)
MODEL_CONFIG = read_json(CONFIG_PATH)
MODEL_CONFIG["dataset_reader"]["dataset_format"] = "txt"
MODEL_CONFIG["chainer"]["pipe"][1]["top_n"] = PARAGRAPHS_NUM
MODEL_CONFIG["dataset_reader"]["data_path"] = "/data/temporary_dataset/"


@app.route("/return_candidates", methods=["POST"])
def return_candidates():
    candidates_list = []
    dialogs = request.json["dialogs"]
    for dialog in dialogs:
        bot_attributes = dialog.get("bot", {}).get("attributes", {})
        db_link = bot_attributes.get("db_link", "")  # where to download model files
        matrix_link = bot_attributes.get("matrix_link", "")
        try:
            logger.info(f"Started downloading files from server (db_link: {db_link}, matrix_link: {matrix_link}).")
            db_file = requests.get(db_link)
            matrix_file = requests.get(matrix_link, timeout=FILE_SERVER_TIMEOUT)
            with open("/data/odqa/userfile.db", "wb") as f:
                f.write(db_file.content)
            with open("/data/odqa/userfile_tfidf_matrix.npz", "wb") as f:
                f.write(matrix_file.content)
            logger.info("Files downloaded successfully.")
            ranker_model = build_model(MODEL_CONFIG)
            logger.info("Model loaded.")
            utterances = dialog.get("human_utterances", [{}])[-1].get("text", "")
            results = ranker_model([utterances])[0]
            candidates_list.append({"candidate_files": results})
        except Exception as e:
            logger.error(e)
            candidates_list.append({})
        logger.info(f"Output candidate files: '{candidates_list}'.")
    return jsonify(candidates_list)


@app.route("/train_and_upload_model", methods=["POST"])
def train_and_upload_model():
    attributes_to_add = []
    dialogs = request.json["dialogs"]
    create_folders_if_not_exist(["/data/documents", "/data/odqa"])
    for dialog in dialogs:
        filepaths_in_container, document_links, docs_and_links = [], [], []
        model_needs_train, doc_needs_upload = False, False
        if dialog.get("human_attributes", [{}])[-1].get("documents", []):
            document_links, model_needs_train = find_and_download_docs_if_needed(
                dialog, model_needs_train, filepaths_in_container, docs_and_links
            )
        elif "document_links" not in dialog.get("bot", {}).get("attributes", {}):
            model_needs_train, doc_needs_upload = True, True
            if "http" in DOC_PATH_OR_LINK[0]:
                logger.info(f"DOC_PATH_OR_LINK: {DOC_PATH_OR_LINK}")
                download_files_and_save_links(DOC_PATH_OR_LINK, filepaths_in_container, docs_and_links)
            else:
                move_files_and_save_paths(DOC_PATH_OR_LINK, filepaths_in_container, docs_and_links)
        logger.info(f"filepaths_in_container: {filepaths_in_container}")
        if model_needs_train:
            try:
                bot_and_human_atts = train_upload_return_attributes(
                    MODEL_CONFIG,
                    filepaths_in_container,
                    document_links,
                    docs_and_links,
                    doc_needs_upload=doc_needs_upload,
                )
                files_to_remove = filepaths_in_container + [
                    "/data/odqa/userfile.db",
                    "/data/odqa/userfile_tfidf_matrix.npz",
                ]
                remove_files_and_folders(files_to_remove, ["/data/temporary_dataset/"])
                attributes_to_add.append(bot_and_human_atts)
                logger.info(f"Attributes in save_model: {attributes_to_add}")
            except Exception as e:
                logger.error(e)
                attributes_to_add.append({})
        else:
            attributes_to_add.append({})
    return jsonify(attributes_to_add)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
