import requests
import logging
import os

from pathlib import PurePath
from deeppavlov import train_model
from common.build_dataset import build_dataset
from common.files_and_folders_processing import upload_document
from typing import List, Dict, Tuple


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

FILE_SERVER_URL = os.environ.get("FILE_SERVER_URL", None)
FILE_SERVER_TIMEOUT = float(os.environ.get("FILE_SERVER_TIMEOUT", 30))


def upload_model_return_id_and_links(db_file: str, matrix_file: str, model_id: str) -> Tuple[str, str]:
    """Uploads the model files to server and returns their ids and links to them.

    Args:
        db_file: Path to file with database.
        matrix_file: Path to file with TF-IDF matrix.

    Returns:
        A link to file with database:

        '{FILE_SERVER_URL}/file?file=lmskdUBH9m_7ed546db9846ba7661ceda123837f7fc.db'

        A link to file with TF-IDF matrix:

        '{FILE_SERVER_URL}/file?file=lmskdUBH9m_7ed546db9846ba7661ceda123837f7fc.npz'
    """
    db_link = upload_document(db_file, f"{model_id}.db", FILE_SERVER_URL, FILE_SERVER_TIMEOUT, type_ref="file")
    matrix_link = upload_document(matrix_file, f"{model_id}.npz", FILE_SERVER_URL, FILE_SERVER_TIMEOUT, type_ref="file")
    return db_link, matrix_link


def download_files(document_links: List[str], filepaths_in_container: List[str]) -> List[str]:
    """Downloads the given files and returns paths to them in container.

    Args:
        document_links: A list of links to file to be downloaded.
        filepaths_in_container: A list of paths to already downloaded files.

    Returns:
        An updated list of paths to downloaded files.
    """
    for link in document_links:
        filename = PurePath(link).name
        filepath_in_container = f"/data/documents/{filename}"
        if not os.path.exists(filepath_in_container):
            orig_file = requests.get(link, timeout=FILE_SERVER_TIMEOUT).text
            with open(filepath_in_container, "w") as f:
                f.write(orig_file)
        filepaths_in_container.append(filepath_in_container)
    return filepaths_in_container


def build_dataset_and_train_model(model_config: dict, filepaths_in_container: List[str]):
    """Builds dataset and fits the TF-IDF vectorizer on it.

    Args:
        model_config: A dictionary with vectorizer config.
        filepaths_in_container: A list of paths to already downloaded files.
    """
    dataset_path = model_config["dataset_reader"]["data_path"]
    logger.info("Files are not vectorized.\nLet's vectorize them!\n")
    build_dataset(dataset_path, filepaths_in_container)
    logger.info("Dataset built. Now vectorizing the files.")
    train_model(model_config)
    logger.info("Files are vectorized.")


def add_file_id_to_config(model_config, file_id):
    """Updates paths in model config to include a unique file id.

    Args:
        model_config: A dictionary with vectorizer config.
        file_id: A unique file id to be added to all paths in config.

    Returns:
        An updated config.
    """
    model_config["dataset_reader"]["data_path"] = f"/data/temporary_dataset_{file_id}/"
    model_config["dataset_iterator"]["load_path"] = f"/data/odqa/userfile_{file_id}.db"
    model_config["dataset_reader"]["save_path"] = f"/data/odqa/userfile_{file_id}.db"
    model_config["chainer"]["pipe"][0]["load_path"] = f"/data/odqa/userfile_tfidf_matrix_{file_id}.npz"
    model_config["chainer"]["pipe"][0]["save_path"] = f"/data/odqa/userfile_tfidf_matrix_{file_id}.npz"
    return model_config


def vectorize_upload_return_attributes(
    model_config: dict, filepaths_in_container: List[str], documents_in_use: List[str], model_id: str
) -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
    """Vectorizes given dataset files using TF-IDF, uploads the resulting files to server
        and saves information about them.

    Args:
        model_config: A dictionary with vectorizer model_config.
        filepaths_in_container: A list of paths to dataset files inside container.
        processed_docs: A dictionary with information about processed documents.

    Returns:
        A dict with information about the model files uploaded to server:
        model_info = {
            'db_link': '{FILE_SERVER_URL}/file?file=lmskdUBH9m_7ed546db9846ba7661ceda123837f7fc.db',
            'matrix_link': '{FILE_SERVER_URL}/file?file=lmskdUBH9m_7ed546db9846ba7661ceda123837f7fc.npz',
            'file_ids': ["nlkr09lnvJ_7ed546db9846ba7661ceda123837f7fc", "kKmcdwiow9_7ed546db9846ba7661ceda123837f7fc"]
            }
    """
    userfile_path = model_config["dataset_iterator"]["load_path"]
    tfidf_matrix_path = model_config["chainer"]["pipe"][0]["load_path"]
    build_dataset_and_train_model(model_config, filepaths_in_container)
    logger.info("Started writing vectorized files to server.")
    db_link, matrix_link = upload_model_return_id_and_links(userfile_path, tfidf_matrix_path, model_id)
    model_info = {"db_link": db_link, "matrix_link": matrix_link, "file_ids": documents_in_use}
    return model_info
