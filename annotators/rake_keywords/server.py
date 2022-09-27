import logging
import time
from os import getenv

import sentry_sdk
from flask import Flask, request, jsonify

from nltk.corpus import stopwords
import RAKE

sentry_sdk.init(getenv("SENTRY_DSN"))


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

stop_words = stopwords.words("english")
rake = RAKE.Rake(stop_words)

logger.info("Model is ready")


def get_keywords(sent):
    words = rake.run(sent.lower(), minFrequency=1, maxWords=1)
    keywords = [word[0] for word in words]
    return keywords


def get_result(request):
    st_time = time.time()
    sentences = request.json["sentences"]
    logger.debug(f"Input sentences: {sentences}")

    nounphrases_batch = [get_keywords(sentence) for sentence in sentences]
    result = [[nounph for nounph in nounphrases if len(nounph)] for nounphrases in nounphrases_batch]

    logger.debug(f"rake_keywords output: {result}")
    total_time = time.time() - st_time
    logger.info(f"rake_keywords exec time: {total_time:.3f}s")
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
    app.run(debug=False, host="0.0.0.0", port=8007)
