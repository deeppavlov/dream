import logging
import os
import sentry_sdk
import random
import string
import requests
import time
import shutil
from deeppavlov import build_model
from urllib.parse import urlparse
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov.core.common.file import read_json
from train_model_if_not_exist import upload_document, train_model

# logging here because it conflicts with tf

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)
# original_document. если лежит, берем его. если нет, чекаем атрибуты. и постоянно чекаем атрибуты на каждом шаге
ORIGINAL_FILES_PATHS = os.environ.get("ORIGINAL_FILES_PATHS", "")
if ORIGINAL_FILES_PATHS:
    ORIGINAL_FILES_PATHS = ORIGINAL_FILES_PATHS.split(",")
CONFIG_PATH = os.environ.get("CONFIG_PATH", None)
SERVICE_PORT = os.environ.get("SERVICE_PORT", None)
FILE_SERVER_URL = os.environ.get("FILE_SERVER_URL", None)
PARAGRAPHS_NUM = 5
server_url = urlparse(FILE_SERVER_URL)
assert CONFIG_PATH, logger.info("No config file name is given.")
assert FILE_SERVER_URL, logger.info("No file server url path is given.")
MODEL_CONFIG = read_json(CONFIG_PATH)
MODEL_CONFIG["dataset_reader"]["dataset_format"] = "txt"
MODEL_CONFIG["chainer"]["pipe"][1]["top_n"] = PARAGRAPHS_NUM


def get_answers(utterance: str, ranker):
    ranker_output = ranker([utterance])
    raw_candidates = ranker_output[0]
    return raw_candidates


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def download_file_to_data(filepath):
    file_id = generate_random_string(10)
    filepath_container = f"/data/documents/{file_id}.txt"
    orig_file = requests.get(filepath, timeout=30)
    with open(filepath_container, "wb") as f:
        f.write(orig_file.content)
    return filepath_container


@app.route("/return_candidates", methods=["POST"])
def return_candidates():
    candidates_list = []
    dialogs = request.json["dialogs"]
    for dialog in dialogs:  
        bot_attributes = dialog.get("bot", {}).get("attributes", {})
        db_link = bot_attributes.get("db_link", "") #where to download model files
        matrix_link = bot_attributes.get("matrix_link", "")
        try:
            logger.info(
                f"Started downloading files from server (db_link: {db_link}, matrix_link: {matrix_link})."
            )
            db_file = requests.get(db_link)
            matrix_file = requests.get(matrix_link, timeout=30)
            # if not os.path.exists("/data/odqa"):
            #     os.mkdir("/data/odqa")
            with open("/data/odqa/userfile.db", "wb") as f:
                f.write(db_file.content)
            with open("/data/odqa/userfile_tfidf_matrix.npz", "wb") as f:
                f.write(matrix_file.content)
            logger.info("Files downloaded successfully.")
            ranker_model = build_model(
                MODEL_CONFIG
            )  # todo: check if it works with config, not path
            logger.info("Model loaded.")
            utterances = dialog.get("human_utterances", [{}])[-1].get(
                "text", ""
            )  # todo: проверить везде смену utterances->human_utterances
            results = get_answers(utterances, ranker_model)
            candidates_list.append(
                {"candidate_files": results}
            )  # todo: write about results
        except Exception as e:
            logger.error(e)
            candidates_list.append(
                {}
            )  # todo: добавить дефолтные значения, посмотреть как это сделано. для одного элемента батча!!!
        logger.info(f"Output candidate files: '{candidates_list}'.")
    return jsonify(candidates_list)


@app.route("/train_and_upload_model", methods=["POST"])
def train_and_upload_model():
    bot_attributes = []
    dialogs = request.json["dialogs"]
    for dialog in dialogs:
        attributes = dialog.get("bot", {}).get("attributes", {})  # todo: batches
        NEED_TRAIN = False # in most cases, we don't re-train the model
        FILE_PATHS_IN_CONTAINER = []
        if not ORIGINAL_FILES_PATHS: # if empty, then it's the dreambuilder option
            if dialog.get("human_attributes", [])[-1].get("documents", []) != attributes.get("document_links", []):
                #if in dreambuilder the list of docs changed compared to previous step
                NEED_TRAIN = True # if list of files changed, then we retrain the model
                if (
                    not ORIGINAL_FILES_PATHS
                ):  # dreambuilder option; file is already on files:3000; url comes in human_attributes
                    DOC_NEEDS_UPLOAD = False # doc is on server already
                    document_links = dialog.get("human_attributes", [])[-1].get(
                        "documents", []
                    )  # we get incoming document links
                    for link in document_links: 
                        filepath_container = download_file_to_data(link)
                        FILE_PATHS_IN_CONTAINER.append(filepath_container) # we download all incoming files to /data and save paths
        if (
            "document_links" not in attributes
        ):  # if there is no document_link in attributes -> the model was never trained
            NEED_TRAIN = True
            logger.info("Started writing files to server.")
            DOC_NEEDS_UPLOAD = True # in all not dreambuilder cases, doc needs to be uploaded to server
            # FILE_ID = generate_random_string(10)
            # FILE_PATH_IN_CONTAINER = f"/data/documents/{FILE_ID}.txt"
            # for filepath in ORIGINAL_FILES_PATHS:
            #     filepath_container = download_file_to_data(filepath) 
            #     FILE_PATHS_IN_CONTAINER.append(filepath_container)
            # if ( #removed it case it's already covered earlier
            #     not ORIGINAL_FILES_PATHS
            # ):  # dreambuilder option, but first; file is already on files:3000; url comes in attributes
            #     document_links = dialog.get("human_attributes", [])[-1].get(
            #         "documents", []
            #     )  # todo: ensure that dialog is okay
            #     assert document_links, logger.info(
            #         "No document path or url provided."
            #     )
            #     for filepath in document_links:
            #         filepath_container = download_file_to_data(filepath)
            #         FILE_PATHS_IN_CONTAINER.append(filepath_container)
            #     DOC_NEEDS_UPLOAD = False  # if the file is on files:3000, then no need to upload again
            if (
                "http" in ORIGINAL_FILES_PATHS[0] #if any element is a link
            ):  # dream option; we get file url, download it, need to upload to files:3000
                for filepath in ORIGINAL_FILES_PATHS:
                    filepath_container = download_file_to_data(filepath) # download all files to data
                    FILE_PATHS_IN_CONTAINER.append(filepath_container) #save paths
            else:  # dream option; we get file path inside our folder, need to upload to files:3000
                for filepath in ORIGINAL_FILES_PATHS:
                    filepath_container = f"/data/documents/"
                    shutil.copyfile(filepath, filepath_container) # move all the files to /data (for uniformness all files are alqays stored there)
                    FILE_PATHS_IN_CONTAINER.append(f"{filepath_container}/{filepath.split('/')[-1]}") # save paths
        if NEED_TRAIN:
            try:  # todo: think what we do with names (db, npz) if ORIGINAL_FILES_PATHS is already a link on server
                train_model(
                    MODEL_CONFIG, f"data/odqa/document_parts", FILE_PATHS_IN_CONTAINER 
                ) # FILE_PATHS_IN_CONTAINER are used to create a database to work with
                MODEL_ID = generate_random_string(10)
                db_link = upload_document(
                    f"{MODEL_ID}.db", "/data/odqa/userfile.db", FILE_SERVER_URL
                )
                matrix_link = upload_document(
                    f"{MODEL_ID}.npz",
                    "/data/odqa/userfile_tfidf_matrix.npz",
                    FILE_SERVER_URL,
                )
                if DOC_NEEDS_UPLOAD: #only if doc is not already on fileserver
                    document_links = []
                    for filepath in FILE_PATHS_IN_CONTAINER:
                        new_filename = filepath.split("/")[-1] # file already has a random-id name (assigned earlier), so we just get it
                        document_link = upload_document(
                            new_filename, filepath, FILE_SERVER_URL
                        )
                        document_links.append(
                            document_link # save all the links to relevant files on server
                        )  # todo add to folder on server!!!
                time.sleep(1)
                # remove all the generated and downloaded files (stateless paradigm)
                os.remove("/data/odqa/userfile.db")
                os.remove("/data/odqa/userfile_tfidf_matrix.npz")
                for filepath in FILE_PATHS_IN_CONTAINER:
                    os.remove(filepath)
                shutil.rmtree(f"data/odqa/document_parts", ignore_errors=True)
                logger.info(
                    "Files successfully written to server. Everyting removed from /data."
                )
                bot_attributes.append(
                    {
                        "bot_attributes": {
                            "db_link": db_link, #todo: maybe replace db_link and matrix_link with MODEL_ID
                            "matrix_link": matrix_link,
                            "document_links": document_links,
                        }
                    }
                )  # todo: check if we need three links, not just id
                logger.info(f"Bot attributes in save_model: {bot_attributes}")
            except Exception as e:
                logger.error(e)
                bot_attributes.append({})
        else:
            bot_attributes.append({})
    return jsonify(bot_attributes)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
