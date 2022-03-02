import logging
import json
import os
import time

import numpy as np
import sentry_sdk
from flask import Flask, jsonify, request


sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


with open("midas_prediction_counters.json", "r") as f:
    counters = json.load(f)


def inference(last_midas_label, return_probas):
    global counters
    # counters['appreciation'] = {'appreciation': 0.09, 'comment': 0.15, 'opinion': 0.39, 'pos_answer': 0.13, ...}
    if return_probas:
        return counters[last_midas_label]
    else:
        # randomly choose with probability
        return np.random.choice(list(counters[last_midas_label].keys()), p=list(counters[last_midas_label].values()))
        # return max(counters[last_midas_label], key=counters[last_midas_label].get)


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    last_midas_labels = request.json["last_midas_labels"]
    return_probas = request.json.get("return_probas", 0)

    result = [inference(midas_label, return_probas) for midas_label in last_midas_labels]

    total_time = time.time() - st_time
    logger.info(f"midas-predictor exec time: {total_time:.3f}s")
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
