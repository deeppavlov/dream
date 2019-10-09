#!/usr/bin/env python

import logging
import time
import uuid
import numpy as np

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

donotknow_answers = ["I really do not know what to answer.",
                     "Sorry, probably, I din't get what you mean.",
                     "I didn't get it. Sorry.",
                     "Let's talk about something else."]


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    sentences = [dialog["utterances"][-1]["text"] for dialog in dialogs_batch]
    session_id = uuid.uuid4().hex
    confidences = []
    responses = []

    for i, dialog in enumerate(dialogs_batch):
        logger.info(f"user_sentence: {sentences[i]}, session_id: {session_id}")
        response = np.random.choice(donotknow_answers)

        responses += [response]
        confidences += [0.5]
        logger.info(f"response: {response}")

    total_time = time.time() - st_time
    logger.info(f'dummy_skill exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
