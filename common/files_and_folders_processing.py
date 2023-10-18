from urllib.parse import urlparse
import requests
import logging
import os
import string
import random
import time

from typing import List

import sentry_sdk

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logger = logging.getLogger(__name__)

SKILLS_USING_DOC = {"dff_meeting_analysis_skill", "dff_document_qa_llm_skill"}


def create_folders_if_not_exist(folders_list: List[str]) -> None:
    """Creates folders if they do not exist.

    Args:
        folders_list: A list of folder paths to create if they are not already present.
    """
    for folder in folders_list:
        if not os.path.exists(folder):
            os.mkdir(folder)


def generate_unique_file_id(n_char: int, dialog_id: str) -> str:
    """Generates unique file id based that consists of two parts: random sequence and dialog id.

    Args:
        n_char: Length of random sequence to be generated.
        dialog_id: id of the current dialog.

    Returns:
        A string to serve as unique file id. The format is as follows: {random_sequence}_{dialog_id}
        NB: random sequence and dialog id are separated by underscore!
    """
    characters = string.ascii_letters + string.digits
    file_id = "".join(random.choices(characters, k=n_char))
    file_and_dialog_id = f"{file_id}_{dialog_id}"
    return file_and_dialog_id


def upload_document(
    file_or_text: str,
    filename: str,
    file_server_url: str,
    file_server_timeout: float,
    type_ref: str = "text",
) -> str:
    """Uploads the file or text as file to given file server.

    Args:
        file_or_text: File or text to be uploaded.
        filename: Name under which the file will be uploaded.
        file_server_url: Url of the server to be used for file uploading.
        file_server_timeout: Timeout of the server to be used for file uploading.
        type_ref: "text" if string is to be uploaded; "file" if file is to be uploaded.

    Returns:
        Download link for the uploaded file:

        '{FILE_SERVER_URL}/file?file=mKnfr13n5n.txt'
    """
    try:
        server_url = urlparse(file_server_url)
        if type_ref == "text":  # check if we receive filepath or pure text
            text_as_bytes = str.encode(file_or_text)  # if text, encode as bytes and then upload
            resp = requests.post(
                file_server_url,
                files={"file": (filename, text_as_bytes)},
                timeout=file_server_timeout,
            )
        else:  # if filepath, upload the file as bytes
            resp = requests.post(
                file_server_url,
                files={"file": (filename, open(file_or_text, "rb"))},
                timeout=file_server_timeout,
            )
        resp.raise_for_status()
        time.sleep(1)
        download_link = resp.json()["downloadLink"]
        download_link = urlparse(download_link)._replace(scheme=server_url.scheme, netloc=server_url.netloc).geturl()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        download_link = ""
    return download_link
