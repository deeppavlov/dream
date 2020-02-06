import os
import time
import threading
from logging import Logger
import wget
import tarfile

from src import get_ner_index, load_model, LDA
from src.consts import UPDATE_PERIOD, UPDATE_ON_START, MODELS_PATH
from src.utils import get_latest

from src.updater.utils import load_data, reduce_bodies


class Updater(object):
    def __init__(self, logger: Logger = None):
        self._texts = None
        self._model = None
        self._lda_model = None
        self._ner_index = None
        self._latest_news = None

        self._is_stopped = True
        self._mutex = threading.Lock()
        self._log = lambda text: logger.info(text) if logger is not None else None

        if not os.path.isdir(MODELS_PATH):
            os.mkdir(MODELS_PATH)

        def worker():
            time_left = UPDATE_PERIOD
            while not self._is_stopped:
                if time_left <= 0:
                    self.load()
                    time_left = UPDATE_PERIOD
                time.sleep(1)
                time_left -= 1

        self._updating_thread = threading.Thread(target=worker)

    def load(self, update: bool = True):
        self._log(f"Updater started data loading.")
        try:
            updated_data_url = "http://files.deeppavlov.ai/alexaprize_data/updated_washington_post_data.tar.gz"
            wget.download(updated_data_url, out="updated_washington_post_data.tar.gz")
            tf = tarfile.open("updated_washington_post_data.tar.gz")
            tf.extractall(path="/src/")
            os.remove("updated_washington_post_data.tar.gz")
        except Exception as e:
            self._log(f"Updater can not update data: {e}")

        texts = load_data()
        model = load_model(texts, update)
        lda_model = LDA(texts, update)
        ner_index = get_ner_index(texts)

        texts = reduce_bodies(texts)
        latest_news = get_latest(texts, return_indices=True)

        with self._mutex:
            self._texts = texts
            self._model = model
            self._lda_model = lda_model
            self._ner_index = ner_index
            self._latest_news = latest_news

        self._log(f"Updater finished data loading.")

    def start(self, update: bool = UPDATE_ON_START):
        fields = [self._texts, self._model, self._lda_model, self._ner_index, self._latest_news]
        if None in fields:
            self.load(update)

        self._is_stopped = False
        self._updating_thread.start()

    def stop(self):
        self._is_stopped = True
        self._updating_thread.join()

    @property
    def texts(self):
        with self._mutex:
            return self._texts

    @property
    def model(self):
        with self._mutex:
            return self._model

    @property
    def lda_model(self):
        with self._mutex:
            return self._lda_model

    @property
    def ner_index(self):
        with self._mutex:
            return self._ner_index

    @property
    def latest_news(self):
        with self._mutex:
            return self._latest_news
