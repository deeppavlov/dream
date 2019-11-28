#!/usr/bin/env python

import logging
import time
import numpy as np

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

donotknow_answers = np.array(["I really do not know what to answer.",
                              "Sorry, probably, I didn't get what you meant.",
                              "I didn't get it. Sorry.",
                              "Let's talk about something else."])

with open("./topical_chat_questions.txt", "r") as f:
    QUESTIONS = f.read().splitlines()


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    final_confidences = []
    final_responses = []

    for dialog in dialogs_batch:
        cands = []
        confs = []

        cands += [np.random.choice(donotknow_answers)]
        confs += [0.5]
        cands += [np.random.choice(QUESTIONS)]
        confs += [0.6]
        final_responses.append(cands)
        final_confidences.append(confs)

    total_time = time.time() - st_time
    logger.info(f'dummy_skill exec time: {total_time:.3f}s')
    return jsonify(list(zip(final_responses, final_confidences)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
