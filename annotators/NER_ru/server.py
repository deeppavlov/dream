import logging
import os
import time

import numpy as np
import sentry_sdk
from flask import Flask, jsonify, request

from deeppavlov import build_model

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

config_name = os.getenv("CONFIG")

try:
    ner_model = build_model(config_name, download=True)
    r = "я видела ивана в москве"
    logger.info(f"Original: {r}. NER: {ner_model([r])}")
    logger.info("ner ru model is loaded.")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


def convert_prediction(s, token, tag):
    start_pos = s.find(token)
    return {
        "confidence": 1,
        "text": token,
        "type": tag.replace("B-", "").replace("I-", ""),
        "start_pos": start_pos,
        "end_pos": start_pos + len(token),
    }


def get_result(request):
    st_time = time.time()
    last_utterances = request.json["last_utterances"]
    logger.info(f"input (the last utterances): {last_utterances}")

    samples = []
    dialog_ids = []
    for i, utterance_sents in enumerate(last_utterances):
        for sent in utterance_sents:
            samples.append(sent)
            dialog_ids.append(i)

    tokens_batch, tags_batch = ner_model(samples)
    good_preds = [
        [convert_prediction(s, token, tag) for token, tag in zip(tokens, tags) if tag != "O"]
        for s, tokens, tags in zip(samples, tokens_batch, tags_batch)
    ]
    dialog_ids = np.array(dialog_ids)

    ret = []
    for i, utterance_sents in enumerate(last_utterances):
        curr_ids = np.where(dialog_ids == i)[0]
        curr_preds = [good_preds[curr_id] for curr_id in curr_ids]
        ret.append(curr_preds)

    logger.info(f"NER output: {ret}")
    total_time = time.time() - st_time
    logger.info(f"NER exec time: {total_time: .3f}s")
    return ret


@app.route("/ner", methods=["POST"])
def respond():
    result = get_result(request)
    return jsonify(result)


@app.route("/ner_batch", methods=["POST"])
def respond_batch():
    result = get_result(request)
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8021)
