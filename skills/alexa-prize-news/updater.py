import logging
import os
import sys
import time
from typing import Callable

from src import TfIdfModel, LDA
from src.consts import UPDATE_PERIOD, UPDATE_ON_START, MODELS_PATH, MODELS_INFO_PATH, UPDATER_LOGS_PATH
from src.updater.utils import load_data
from src.utils import save, load


def train(log: Callable[[str], None]):
    log("Starting training.")

    texts = load_data()
    LDA(log).update(texts).save()
    TfIdfModel(log).update_and_save(texts)
    save(MODELS_INFO_PATH, {"last_trained": last_trained})

    log("Finishing training.")


if __name__ == '__main__':
    logger = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s %(message)s")
    fh = logging.FileHandler(UPDATER_LOGS_PATH)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    if not os.path.isdir(MODELS_PATH):
        os.mkdir(MODELS_PATH)

    logger.warning("Updater started.")
    info = load(MODELS_INFO_PATH)
    last_trained = 0 if UPDATE_ON_START or info is None else time.time()
    while True:
        if time.time() - last_trained > UPDATE_PERIOD:
            last_trained = time.time()
            train(logger.warning)
        time.sleep(1)
