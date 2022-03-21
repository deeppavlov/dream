import logging
import re
import time
from os import getenv

import sentry_sdk
import spacy
from flask import Flask, request, jsonify


sentry_sdk.init(getenv("SENTRY_DSN"))

spacy_nlp = spacy.load(getenv("SPACY_MODEL"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def get_result(request):
    st_time = time.time()
    sentences = request.json["sentences"]
    logger.debug(f"Input sentences: {sentences}")

    nounphrases_batch = [noun_phrase_extraction(sentence) for sentence in sentences]
    nounphrases_batch = [
        [re.sub(symbols_for_nounphrases, "", nounph).strip() for nounph in nounphrases]
        for nounphrases in nounphrases_batch
    ]
    nounphrases_batch = [[re.sub(spaces, " ", nounph) for nounph in nounphrases] for nounphrases in nounphrases_batch]
    result = [[nounph for nounph in nounphrases if len(nounph)] for nounphrases in nounphrases_batch]

    total_time = time.time() - st_time
    logger.info(f"spacy_annotator exec time: {total_time:.3f}s")
    return result


@app.route("/respond", methods=["POST"])
def nounphrases_respond():
    result = get_result(request)
    return jsonify(result)


@app.route("/respond_batch", methods=["POST"])
def nounphrases_respond_batch():
    result = get_result(request)
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
