import requests
import logging
import os
import random
import string
import time
import shutil
import pypdfium2 as pdfium

from pathlib import PurePath
from bs4 import BeautifulSoup
from deeppavlov import train_model
from common.build_dataset import build_dataset
from urllib.parse import urlparse


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

FILE_SERVER_URL = os.environ.get("FILE_SERVER_URL", None)
FILE_SERVER_TIMEOUT = int(os.environ.get("FILE_SERVER_TIMEOUT", 30))


def find_and_download_docs_if_needed(dialog, model_needs_train, filepaths_in_container, docs_and_links):
    if "human_attributes" in dialog:
        document_links_in_attr = dialog.get("human_attributes", [{}])[-1].get("documents", [])  # new docs
        processed_docs = dialog.get("bot", {}).get("attributes", {}).get("document_links", [])
        if document_links_in_attr != processed_docs:
            model_needs_train = True
            download_files_and_save_links(document_links_in_attr, filepaths_in_container, docs_and_links)
    else:
        logger.info("No documents found anywhere.")
    return document_links_in_attr, model_needs_train


def train_upload_return_attributes(
    config, filepaths_in_container, document_links, docs_and_links, doc_needs_upload=False
):
    logger.info("Started training model.")
    build_dataset_and_train_model(
        config, "/data/temporary_dataset/", filepaths_in_container
    )  # filepaths_in_container are used to create a database to work with
    logger.info("Started writing model files to server.")
    model_id, db_link, matrix_link = upload_model_return_id_and_links(
        "/data/odqa/userfile.db", "/data/odqa/userfile_tfidf_matrix.npz"
    )
    if doc_needs_upload:  # only if doc is not already on fileserver
        document_links = upload_files_return_links(filepaths_in_container)
    time.sleep(1)
    bot_and_human_atts = {
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
    return bot_and_human_atts


def upload_model_return_id_and_links(db_file, matrix_file):
    model_id = generate_random_string(10)
    db_link = upload_document(f"{model_id}.db", db_file, FILE_SERVER_URL)
    matrix_link = upload_document(f"{model_id}.npz", matrix_file, FILE_SERVER_URL)
    return model_id, db_link, matrix_link


def upload_files_return_links(filepaths_in_container):
    document_links = []
    for filepath in filepaths_in_container:
        new_filename = PurePath(filepath).name
        # file already has a random-id name (assigned earlier), so we just get it
        document_link = upload_document(new_filename, filepath, FILE_SERVER_URL)
        document_links.append(document_link)
        # save all the links to relevant files on server
        # todo: in the future add to folder on server!!!
    return document_links


def create_folders_if_not_exist(folders_list):
    for folder in folders_list:
        if not os.path.exists(folder):
            os.mkdir(folder)


def remove_files_and_folders(files_list, folders_list):
    for file in files_list:
        os.remove(file)
    for folder in folders_list:
        shutil.rmtree(folder, ignore_errors=True)
    logger.info("Files successfully written to server. Everyting removed from /data.")


def download_files_and_save_links(document_links, filepaths_in_container, docs_and_links):
    for link in document_links:
        filepath_in_container = download_file_to_data(link)
        filepaths_in_container.append(filepath_in_container)
        # we download all incoming files to /data and save paths
        docs_and_links.append(
            {
                "document_id": PurePath(link).stem,
                "initial_path_or_link": link,
            }
        )  # linking ids and initial file information


def move_files_and_save_paths(document_paths, filepaths_in_container, docs_and_links):
    for filepath in document_paths:
        file_id = generate_random_string(10)
        filepath_in_container = f"/data/documents/{file_id}.txt"
        orig_file_text = get_text_from_filepath(filepath)
        with open(filepath_in_container, "w") as f:
            f.write(orig_file_text)
        # move all the files to /data (for uniformness all files are always stored there)
        docs_and_links.append(
            {
                "document_id": PurePath(filepath_in_container).stem,
                "initial_path_or_link": filepath,
            }
        )  # linking ids and initial filenames
        filepaths_in_container.append(filepath_in_container)  # save paths


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
    file_extension = PurePath(filepath).suffix
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
    file_extension = PurePath(filepath).suffix
    filepath_in_container = f"/data/documents/{file_id}.txt"
    orig_file = requests.get(filepath, timeout=FILE_SERVER_TIMEOUT)
    orig_file_text = get_text_from_fileobject(orig_file, file_extension)
    with open(filepath_in_container, "w") as f:
        f.write(orig_file_text)
    return filepath_in_container


def upload_document(filename, filepath, file_server_url):
    server_url = urlparse(file_server_url)
    resp = requests.post(file_server_url, files={"file": (filename, open(filepath, "rb"))}, timeout=30)
    resp.raise_for_status()
    download_link = resp.json()["downloadLink"]
    download_link = urlparse(download_link)._replace(scheme=server_url.scheme, netloc=server_url.netloc).geturl()
    return download_link


def build_dataset_and_train_model(model_config, dataset_path, doc_path_or_link):
    print("Model is not trained.\nLet's train the model!\n\n")
    build_dataset(dataset_path, doc_path_or_link)
    print("Dataset built. Now training the model.")
    train_model(model_config)
    print("Model is trained.")
