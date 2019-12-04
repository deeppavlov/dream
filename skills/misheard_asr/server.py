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

misheard_responses = np.array(["Excuse me, I misheard you. Could you repeat that, please?",
                               "I couldn't hear you. Could you say that again, please?",
                               "Sorry, I didn't catch that. Could you say it again, please?"
                               ])


@app.route("/misheard_respond", methods=['POST'])
def misheard_response():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    final_confidences = []
    final_responses = []

    for dialog in dialogs_batch:
        final_responses.append([np.random.choice(misheard_responses)])
        final_confidences.append([1.0])

    total_time = time.time() - st_time
    logger.info(f'misheard_asr#misheard_respond exec time: {total_time:.3f}s')
    return jsonify(list(zip(final_responses, final_confidences)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
