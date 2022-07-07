#!/usr/bin/env python

import logging
import time

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

from meta_script import respond_meta_script
from comet_dialog import respond_comet_dialog


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/meta_script", methods=["POST"])
def meta_script():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    final_responses, final_confidences, final_attributes = respond_meta_script(dialogs_batch)

    total_time = time.time() - st_time
    logger.info(f"meta_script_skill exec time: {total_time:.3f}s")
    return jsonify(list(zip(final_responses, final_confidences, final_attributes)))


@app.route("/comet_dialog", methods=["POST"])
def comet_dialog():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    final_responses, final_confidences, final_attributes = respond_comet_dialog(dialogs_batch)

    total_time = time.time() - st_time
    logger.info(f"comet_dialog_skill exec time: {total_time:.3f}s")
    return jsonify(list(zip(final_responses, final_confidences, final_attributes)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
