#!/usr/bin/env python

import logging
import re
import time
import random

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk
from deeppavlov import build_model

from common.factoid import DONT_KNOW_ANSWER

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

FACTOID_DUMMY_ANSWER_CONFIDENCE = 0.95
factiod_classifier = build_model(config="./yahoo_convers_vs_info_light.json", download=False)

tell_me = r"(do you know|(can|could) you tell me|tell me)"
tell_me_template = re.compile(tell_me)
full_template = re.compile(tell_me + r" (who|where|when|what|why)")


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    confidences = []
    responses = []
    attributes = []

    sentences_to_classify = []
    for dialog in dialogs_batch:
        sentences_to_classify.append(dialog["human_utterances"][-1]["text"])

    sentences_to_classify = [re.sub(tell_me_template, "", sent).strip()
                             if re.findall(full_template, sent) else sent
                             for sent in sentences_to_classify]
    # "0" - factoid; "1" - conversational
    factoid_classes = factiod_classifier(sentences_to_classify)
    factoid_classes = [True if cl == ["0"] else False for cl in factoid_classes]

    for dialog, is_factoid in zip(dialogs_batch, factoid_classes):
        if is_factoid and "?" in dialog["human_utterances"][-1]["text"]:
            logger.info(f"Factoid question. Answer dummy response.")
            response = random.choice(DONT_KNOW_ANSWER)
            confidence = FACTOID_DUMMY_ANSWER_CONFIDENCE
        else:
            response = ""
            confidence = 0.

        attr = {}

        responses.append(response)
        confidences.append(confidence)
        attributes.append(attr)

    total_time = time.time() - st_time
    logger.info(f'factoid_qa exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences, attributes)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
