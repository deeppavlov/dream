import requests
import os

from deeppavlov import train_model
from common.build_dataset import build_dataset
from urllib.parse import urlparse


def upload_document(filename, filepath, file_server_url):
    server_url = urlparse(file_server_url)
    resp = requests.post(
        file_server_url, files={"file": (filename, open(filepath, "rb"))}, timeout=30
    )
    resp.raise_for_status()
    download_link = resp.json()["downloadLink"]
    download_link = (
        urlparse(download_link)
        ._replace(scheme=server_url.scheme, netloc=server_url.netloc)
        .geturl()
    )
    return download_link


# перенести это все в сервер.пай ((( сделать функцией, импортнуть
def build_dataset_and_train_model(model_config, dataset_path, ORIGINAL_FILES_PATHS):
    print("Model is not trained.\nLet's train the model!\n\n")
    build_dataset(dataset_path, ORIGINAL_FILES_PATHS)
    # for filename in os.listdir(dataset_path):
    #     with open(os.path.join(os.getcwd(), filename), 'r') as f: 

    print("Dataset built. Now training the model.")
    train_model(model_config)
    print("Model is trained.")
