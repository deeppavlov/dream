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
                              "Sorry, probably, I didn't get what you mean.",
                              "I didn't get it. Sorry.",
                              "Let's talk about something else."])


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    confidences = []
    responses = []

    responses = np.random.choice(donotknow_answers, size=len(dialogs_batch)).tolist()
    confidences = [0.5] * len(dialogs_batch)

    total_time = time.time() - st_time
    logger.info(f'dummy_skill exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
