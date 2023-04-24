import json
import logging
import os
from itertools import chain
from typing import List
import nltk.data

# import numpy as np
import sentry_sdk
from deeppavlov import build_model
from deeppavlov.core.commands.utils import parse_config, expand_path
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from utils import get_regexp, unite_responses

# logging here because it conflicts with tf
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)
DATASET_PATH = os.environ.get("DATASET_PATH", None)
ORIGINAL_FILE_PATH = os.environ.get("ORIGINAL_FILE_PATH", None)


CONFIG_PATH = os.environ.get("CONFIG_PATH", None)
DATASET_PATH = os.environ.get("DATASET_PATH", None)
if CONFIG_PATH is None:
    raise NotImplementedError("No config file name is given.")
if DATASET_PATH is None:
    raise NotImplementedError("No dataset path name is given.")

try:
    ranker_model = build_model(CONFIG_PATH)
    logger.info("Model loaded")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


def build_dataset():
    if not os.path.exists(DATASET_PATH):
        os.mkdir(DATASET_PATH)
    tokenizer = nltk.data.load("tokenizers/punkt/english.pickle")
    with open(ORIGINAL_FILE_PATH, "r") as f:
        i = 0
        buf = ""
        data = f.read()
        data = tokenizer.tokenize(data)

        for item in data:
            buf += item
            words = buf.split(" ")
            # сохраняем буфер в файл, если в буфере больше 100 слов
            if len(words) > 100:
                i += 1
                new_f = DATASET_PATH + str(i) + ".txt"
                with open(new_f, "w") as f_out:
                    f_out.write(buf)
                buf = ""
                print(f"creating {DATASET_PATH + str(i) + '.txt'}")


def get_answers(utterance, ranker):
    ranker_output = ranker(utterance)[0]
    candidates = []
    for f_name in ranker_output:
        with open(DATASET_PATH + f_name) as f:
            candidates.append(f.read())
    return " ".join(candidates)


@app.route("/rank", methods=["POST"])
def detect():
    build_dataset()
    utterances = request.json["sentences"][-1]
    logger.info(os.getcwd())
    logger.info(f"Input: `{utterances}`.")
    results = get_answers(utterances, ranker_model)
    logger.info(f"Output: `{results}`.")
    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8200)
