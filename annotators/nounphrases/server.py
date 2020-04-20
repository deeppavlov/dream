#!/usr/bin/env python

import logging
import time
import re

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

from remote_module import noun_phrase_extraction

sentry_sdk.init(getenv('SENTRY_DSN'))


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

symbols_for_nounphrases = re.compile(r"[^0-9a-zA-Z \-]+")
spaces = re.compile(r"\s\s+")


@app.route("/nounphrases", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json['dialogs']
    sentences = [dialog["utterances"][-1]["text"] for dialog in dialogs_batch]

    nounphrases = [noun_phrase_extraction(sent) for sent in sentences]

    for i, sent in enumerate(sentences):
        logger.info(f"user_sentence: {sent}")
        if nounphrases[i] is None:
            nounphrases[i] = []
        for j in range(len(nounphrases[i])):
            nounphrases[i][j] = re.sub(symbols_for_nounphrases, "", nounphrases[i][j]).strip()
            nounphrases[i][j] = re.sub(spaces, " ", nounphrases[i][j])
        nounphrases[i] = [el for el in nounphrases[i] if len(el) > 0]
        logger.info(f"Nouns: {nounphrases[i]}")

    total_time = time.time() - st_time
    logger.info(f'cobot_nounphrasess exec time: {total_time:.3f}s')
    return jsonify(nounphrases)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
