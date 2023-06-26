import logging
import os
import sentry_sdk
import random
import string
import requests
import time
import shutil
import pypdfium2 as pdfium
from bs4 import BeautifulSoup
from deeppavlov import build_model
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov.core.common.file import read_json
from utils import upload_document, build_dataset_and_train_model

# logging here because it conflicts with tf

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)

PARAGRAPHS_NUM = 5
DOC_PATH_OR_LINK = os.environ.get("DOC_PATH_OR_LINK", "")
if DOC_PATH_OR_LINK:
    DOC_PATH_OR_LINK = DOC_PATH_OR_LINK.split(",")  # we may have multiple files
CONFIG_PATH = os.environ.get("CONFIG_PATH", None)
SERVICE_PORT = os.environ.get("SERVICE_PORT", None)
FILE_SERVER_URL = os.environ.get("FILE_SERVER_URL", None)
MODEL_CONFIG = read_json(CONFIG_PATH)
MODEL_CONFIG["dataset_reader"]["dataset_format"] = "txt"
MODEL_CONFIG["chainer"]["pipe"][1]["top_n"] = PARAGRAPHS_NUM
MODEL_CONFIG["dataset_reader"]["data_path"] = "/data/temporary_dataset/"


def get_extension(filepath):
    _, file_extension = os.path.splitext(filepath)
    return file_extension


def get_filename(filepath):
    filename, _ = os.path.splitext(filepath)
    return filename


def pdf_to_text(file):
    pdf = pdfium.PdfDocument(file)  # supports file path strings, bytes, and byte buffers
    n_pages = len(pdf)
    full_doc_text = ""
    for page in range(n_pages):
        page_index = pdf[page]
        textpage = page_index.get_textpage()
        text_all = textpage.get_text_range()
        full_doc_text += text_all
    return full_doc_text


def html_to_text(file):
    soup = BeautifulSoup(file)
    full_doc_text = soup.get_text(strip=True)
    return full_doc_text


def get_text_from_filepath(filepath: str) -> str:
    file_extension = get_extension(filepath)
    if "pdf" in file_extension:
        full_doc_text = pdf_to_text(filepath)
    elif "html" in file_extension:
        with open(filepath, "r") as f:
            html_doc = f.read()
        full_doc_text = html_to_text(html_doc)
    else:
        with open(filepath, "r") as f:
            full_doc_text = f.read()
    return full_doc_text


def get_text_from_fileobject(file_object: str, file_extension: str) -> str:
    if "pdf" in file_extension:
        full_doc_text = pdf_to_text(file_object.content)
    elif "html" in file_extension:
        full_doc_text = html_to_text(file_object.text)
    else:
        full_doc_text = file_object.text
    return full_doc_text


def generate_random_string(length: int) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def download_file_to_data(filepath: str) -> str:
    file_id = generate_random_string(10)
    file_extension = get_extension(filepath)
    filepath_in_container = f"/data/documents/{file_id}.txt"
    orig_file = requests.get(filepath, timeout=30)
    orig_file_text = get_text_from_fileobject(orig_file, file_extension)
    with open(filepath_in_container, "w") as f:
        f.write(orig_file_text)
    return filepath_in_container


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
            matrix_file = requests.get(matrix_link, timeout=30)
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
    docs_and_links = []  # list with dict of ids - original links/paths
    if not os.path.exists("/data/documents"):
        os.mkdir("/data/documents")
    if not os.path.exists("/data/odqa"):
        os.mkdir("/data/odqa")
    for dialog in dialogs:
        attributes = dialog.get("bot", {}).get("attributes", {})
        model_needs_train = False  # in most cases, we don't re-train the model
        filepaths_in_container = []
        if (
            not DOC_PATH_OR_LINK
        ):  # if empty, then it's the dreambuilder option - file is already on files:3000; url comes in human_attributes
            if dialog.get("human_attributes", []):
                if dialog.get("human_attributes", [])[-1].get("documents", []) != attributes.get(
                    "document_links", []
                ):  # if in dreambuilder the list of docs changed compared to previous step
                    model_needs_train = True  # if list of files changed, then we need to retrain the model
                    doc_needs_upload = False  # doc is on server already
                    document_links = dialog.get("human_attributes", [])[-1].get(
                        "documents", []
                    )  # we get incoming document links
                    for link in document_links:
                        filepath_in_container = download_file_to_data(link)
                        filepaths_in_container.append(filepath_in_container)
                        # we download all incoming files to /data and save paths
                        docs_and_links.append(
                            {
                                "document_id": get_filename(link).split("/")[-1],
                                "initial_path_or_link": link,
                            }
                        )
                        # linking ids and initial links
            else:
                logger.info("No documents specified in human_attributes.")
        if (
            "document_links" not in attributes
        ):  # if there is no document_link in bot attributes -> the model was never trained
            model_needs_train = True
            doc_needs_upload = True  # in all not dreambuilder cases, doc needs to be uploaded to server
            if "http" in DOC_PATH_OR_LINK[0]:  # if any element is a link
                # dream option; we get file url, download it, need to upload to files:3000
                for filepath in DOC_PATH_OR_LINK:
                    filepath_in_container = download_file_to_data(filepath)
                    # download all files to data
                    docs_and_links.append(
                        {
                            "document_id": get_filename(filepath_in_container).split("/")[-1],
                            "initial_path_or_link": filepath,
                        }
                    )
                    # linking ids and initial links
                    filepaths_in_container.append(filepath_in_container)  # save paths
            else:  # dream option; we get file path inside our folder, need to upload to files:3000
                for filepath in DOC_PATH_OR_LINK:
                    file_id = generate_random_string(10)
                    filepath_in_container = f"/data/documents/{file_id}.txt"
                    orig_file_text = get_text_from_filepath(filepath)
                    with open(filepath_in_container, "w") as f:
                        f.write(orig_file_text)
                    # shutil.copyfile(filepath, filepath_in_container)
                    # move all the files to /data (for uniformness all files are always stored there)
                    docs_and_links.append(
                        {
                            "document_id": get_filename(filepath_in_container).split("/")[-1],
                            "initial_path_or_link": filepath,
                        }
                    )  # linking ids and initial filenames
                    filepaths_in_container.append(filepath_in_container)  # save paths
        logger.info(f"filepaths_in_container: {filepaths_in_container}")
        if model_needs_train:
            try:
                logger.info("Started training model.")
                build_dataset_and_train_model(
                    MODEL_CONFIG, "/data/temporary_dataset/", filepaths_in_container
                )  # filepaths_in_container are used to create a database to work with
                logger.info("Started writing model files to server.")
                model_id = generate_random_string(10)
                db_link = upload_document(f"{model_id}.db", "/data/odqa/userfile.db", FILE_SERVER_URL)
                matrix_link = upload_document(
                    f"{model_id}.npz",
                    "/data/odqa/userfile_tfidf_matrix.npz",
                    FILE_SERVER_URL,
                )
                if doc_needs_upload:  # only if doc is not already on fileserver
                    document_links = []
                    for filepath in filepaths_in_container:
                        new_filename = filepath.split("/")[-1]
                        # file already has a random-id name (assigned earlier), so we just get it
                        document_link = upload_document(new_filename, filepath, FILE_SERVER_URL)
                        document_links.append(document_link)
                        # save all the links to relevant files on server
                        # todo: in the future add to folder on server!!!
                time.sleep(1)
                # remove all the generated and downloaded files (stateless paradigm)
                os.remove("/data/odqa/userfile.db")
                os.remove("/data/odqa/userfile_tfidf_matrix.npz")
                for filepath in filepaths_in_container:
                    os.remove(filepath)
                shutil.rmtree("/data/temporary_dataset/", ignore_errors=True)
                logger.info("Files successfully written to server. Everyting removed from /data.")
                attributes_to_add.append(
                    {
                        "bot_attributes": {
                            "db_link": db_link,  # todo: maybe replace db_link and matrix_link with model_id
                            "matrix_link": matrix_link,
                            "document_links": document_links,
                        },
                        "human_attributes": {
                            "documents_qa_model": {
                                "model_id": model_id,
                                "document_ids_and_info": docs_and_links,
                                "document_links": document_links,
                            }
                        },
                    }
                )
                logger.info(f"Attributes in save_model: {attributes_to_add}")
            except Exception as e:
                logger.error(e)
                attributes_to_add.append({})
        else:
            attributes_to_add.append({})
    return jsonify(attributes_to_add)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
