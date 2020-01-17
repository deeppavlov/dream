import time
import threading
from logging import Logger

from src import get_ner_index, TfIdfModel, LDA
from src.consts import MODELS_INFO_PATH
from src.updater.utils import load_data, reduce_bodies
from src.utils import get_latest, load


class Loader(object):
    def __init__(self, logger: Logger = None):
        self._log = lambda text: logger.warning(text) if logger is not None else None

        self._texts = None
        self._tf_idf_model = None
        self._lda_model = None
        self._ner_index = None
        self._latest_news = None

        self._last_loaded = None
        self._is_stopped = True
        self._mutex = threading.Lock()

        def worker():
            while not self._is_stopped:
                if self.recent_models_available():
                    self._load()
                    self._last_loaded = time.time()
                time.sleep(1)

        self._updating_thread = threading.Thread(target=worker)

    def _load(self):
        texts = load_data()
        tf_idf_model = TfIdfModel(self._log).load()
        lda_model = LDA(self._log).load()
        ner_index = get_ner_index(texts)

        texts = reduce_bodies(texts)
        latest_news = get_latest(texts, return_indices=True)

        with self._mutex:
            self._texts = texts
            self._tf_idf_model = tf_idf_model
            self._lda_model = lda_model
            self._ner_index = ner_index
            self._latest_news = latest_news

    def start(self):
        while not self.recent_models_available():
            self._log("Waiting for models...")
            time.sleep(60)

        self._load()
        self._is_stopped = False
        self._updating_thread.start()

    def stop(self):
        self._is_stopped = True
        self._updating_thread.join()

    def recent_models_available(self):
        info = load(MODELS_INFO_PATH)
        return info is not None and (self._last_loaded is None or self._last_loaded < info["last_trained"])

    @property
    def texts(self):
        with self._mutex:
            return self._texts

    @property
    def model(self):
        with self._mutex:
            return self._tf_idf_model

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
