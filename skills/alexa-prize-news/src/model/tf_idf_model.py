import os
import shutil
from typing import Callable

from deeppavlov import train_model, build_model
from deeppavlov.core.common.file import read_json

from src.consts import (
    TF_IDF_MODEL_CONFIG_PATH,
    TF_IDF_MODEL_READER_PATH,
    TF_IDF_MODEL_CHAINER_PATH,
    TF_IDF_MODEL_TMP_PATH,
)


class TfIdfModel(object):
    def __init__(self, log: Callable[[str], None]):
        self._model = None
        self._log = log

        self.model_config = read_json(TF_IDF_MODEL_CONFIG_PATH)
        self.model_config["dataset_reader"]["data_path"] = TF_IDF_MODEL_TMP_PATH + "/"
        self.model_config["dataset_reader"]["save_path"] = TF_IDF_MODEL_READER_PATH
        self.model_config["dataset_iterator"]["load_path"] = TF_IDF_MODEL_READER_PATH
        self.model_config["chainer"]["pipe"][0]["save_path"] = TF_IDF_MODEL_CHAINER_PATH
        self.model_config["chainer"]["pipe"][0]["load_path"] = TF_IDF_MODEL_CHAINER_PATH

    def __call__(self, *args):
        return self._model(*args)

    def update_and_save(self, texts):
        self._log("Starting TF-IDF model training.")

        if not os.path.isdir(TF_IDF_MODEL_TMP_PATH):
            os.mkdir(TF_IDF_MODEL_TMP_PATH)
        for i, file in enumerate(texts):
            with open(TF_IDF_MODEL_TMP_PATH + f"/{i}", "w", encoding="utf-8") as b:
                if "headline" in file:
                    b.write(file["headline"])

        self._model = train_model(self.model_config)
        shutil.rmtree(TF_IDF_MODEL_TMP_PATH)

        self._log("Finishing TF-IDF model training.")
        return self

    def load(self):
        self._model = build_model(self.model_config, load_trained=True)
        return self
