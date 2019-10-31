#!/usr/bin/env python

import logging
import uuid
import time

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

from remote_module import noun_phrase_extraction

sentry_sdk.init(getenv('SENTRY_DSN'))


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/nounphrases", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json['dialogs']
    sentences = [dialog["utterances"][-1]["text"] for dialog in dialogs_batch]
    session_id = uuid.uuid4().hex

    nounphrases = [noun_phrase_extraction(sent) for sent in sentences]

    for i, sent in enumerate(sentences):
        logger.info(f"user_sentence: {sent}, session_id: {session_id}")

        logger.info(f"Nouns: {nounphrases[i]}")

    total_time = time.time() - st_time
    logger.info(f'cobot_nounphrasess exec time: {total_time:.3f}s')
    return jsonify(nounphrases)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
