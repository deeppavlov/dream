import logging
import time
from os import getenv

import ner_model
import sentry_sdk
from flask import Flask, jsonify, request
from nltk.tokenize import word_tokenize

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

ner = ner_model.load_model()
logger.info("ner model is loaded.")


@app.route('/ner', methods=['POST'])
def respond():
    st_time = time.time()
    last_utterances = request.json["last_utterances"]
    logger.info(f"input (the last utterances): {last_utterances}")

    ret = []
    for utterance in last_utterances:
        sents = [word_tokenize(sent.lower()) for sent in utterance]
        ret.append(ner.predict(sents))

    logger.info(f"NER output: {ret}")

    total_time = time.time() - st_time
    logger.info(f'NER exec time: {total_time: .3f}s')
    return jsonify(ret)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8021)
