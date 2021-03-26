import logging
import time
# import random
# import re
# import json

from flask import Flask, request, jsonify
# from os import getenv

from deeppavlov import build_model
from deeppavlov.core.common.file import read_json


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


class FaqWrapper():
    def __init__(self, faq_config_path):
        faq_config = read_json(f"{faq_config_path}/faq_config.json")
        self.faq = build_model(faq_config, download=True)

    def __call__(self, sentence):
        faq_response = self.faq([sentence])

        response = faq_response[0][0]
        confidences = faq_response[1][0]

        confidence = max(confidences)

        logger.info("faq_skill: response=" + response)
        logger.info("faq_skill: confidence=" + str(confidence))

        # confidence = 1.0  # should it be 1.0 or not?
        # confidence = confidence.astype(float)
        return response, confidence


faq = FaqWrapper("dp_minimal_demo_dir")


@app.route("/test", methods=["POST"])
def test():
    sentence = request.json["sentence"]

    response, conf = faq(sentence)

    return str(response)
    # return request.json["sentence"]


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    dialogs = request.json["dialogs"]

    responses = []
    confidences = []

    for dialog in dialogs:
        sentence = dialog['human_utterances'][-1]['annotations'].get(
            "spelling_preprocessing")

        if sentence is None:
            logger.warning('Not found spelling preprocessing annotation')
            sentence = dialog['human_utterances'][-1]['text']

        response, conf = faq(sentence)

        responses.append(response)
        confidences.append(conf)

    total_time = time.time() - st_time
    logger.info(
        f"faq_skill exec time = {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
