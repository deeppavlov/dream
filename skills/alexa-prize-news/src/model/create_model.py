import os
import pickle
import shutil

from deeppavlov import train_model
from deeppavlov.core.common.file import read_json

from src.consts import (
    TF_IDF_MODEL_PATH,
    TF_IDF_MODEL_CONFIG_PATH,
    TF_IDF_MODEL_READER_PATH,
    TF_IDF_MODEL_CHAINER_PATH,
    TF_IDF_MODEL_TMP_PATH,
)


def load_model(texts, update=True):
    if not update and os.path.isfile(TF_IDF_MODEL_PATH):
        with open(TF_IDF_MODEL_PATH, "rb") as f:
            return pickle.load(f)

    if not os.path.isdir(TF_IDF_MODEL_TMP_PATH):
        os.mkdir(TF_IDF_MODEL_TMP_PATH)
    for i, file in enumerate(texts):
        with open(TF_IDF_MODEL_TMP_PATH + f"/{i}", "w", encoding="utf-8") as b:
            if "headline" in file:
                b.write(file["headline"])

    model_config = read_json(TF_IDF_MODEL_CONFIG_PATH)
    model_config["dataset_reader"]["data_path"] = TF_IDF_MODEL_TMP_PATH + "/"
    model_config["dataset_reader"]["save_path"] = TF_IDF_MODEL_READER_PATH
    model_config["dataset_iterator"]["load_path"] = TF_IDF_MODEL_READER_PATH
    model_config["chainer"]["pipe"][0]["save_path"] = TF_IDF_MODEL_CHAINER_PATH
    model_config["chainer"]["pipe"][0]["load_path"] = TF_IDF_MODEL_CHAINER_PATH

    model = train_model(model_config)

    with open(TF_IDF_MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    shutil.rmtree(TF_IDF_MODEL_TMP_PATH)

    return model
