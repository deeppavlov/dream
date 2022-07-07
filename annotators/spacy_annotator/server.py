import logging
import re
import time
from os import getenv

import sentry_sdk
import spacy
from flask import Flask, request, jsonify


sentry_sdk.init(getenv("SENTRY_DSN"))

spacy_nlp = spacy.load(getenv("SPACY_MODEL"))
TOKEN_ATTRIBUTES = getenv("TOKEN_ATTRIBUTES").split("|")
ANNOTATE_BATCH_WITH_TOKENS_ONLY = getenv("ANNOTATE_BATCH_WITH_TOKENS_ONLY", False)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def remove_quotes(text):
    return re.sub(r"\s+", " ", re.sub(r"\'\"", " ", text)).strip()


def get_result(request, only_tokens=False):
    st_time = time.time()
    sentences = request.json["sentences"]
    result = []

    for uttr in sentences:
        doc = spacy_nlp(remove_quotes(uttr))
        curr_tokens = []
        for token in doc:
            curr_token = {"text": token.text}
            if not only_tokens:
                for attr in TOKEN_ATTRIBUTES:
                    curr_token[attr] = str(getattr(token, attr))
            curr_tokens += [curr_token]
        result += [curr_tokens]
    total_time = time.time() - st_time
    logger.info(f"spacy_annotator exec time: {total_time:.3f}s")
    return result


@app.route("/respond", methods=["POST"])
def respond():
    result = get_result(request)
    return jsonify(result)


@app.route("/respond_batch", methods=["POST"])
def respond_batch():
    result = get_result(request, only_tokens=ANNOTATE_BATCH_WITH_TOKENS_ONLY)
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
