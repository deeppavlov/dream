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
    logger.info("NER model is loaded.")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


def convert_prediction(sents, pred_labels):
    entities = []
    for sent, tags in zip(sents, pred_labels):
        entities.append([])
        start = end = -1
        for i, (word, tag) in enumerate(zip(sent, tags)):
            if tag[0] == "B":
                if start != -1:
                    entities[-1].append(
                        {
                            "start_pos": start,
                            "end_pos": end,
                            "type": tags[start].split("-")[1],
                            "text": " ".join(sent[start:end]),
                            "confidence": 1,
                        }
                    )
                start = i
                end = i + 1
            elif tag[0] == "I":
                end = i + 1
            else:
                if start != -1:
                    entities[-1].append(
                        {
                            "start_pos": start,
                            "end_pos": end,
                            "type": tags[start].split("-")[1],
                            "text": " ".join(sent[start:end]),
                            "confidence": 1,
                        }
                    )
                    start = -1
        if start != -1:
            entities[-1].append(
                {
                    "start_pos": start,
                    "end_pos": end,
                    "type": tags[start].split("-")[1],
                    "text": " ".join(sent[start:end]),
                    "confidence": 1,
                }
            )
    return entities


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
    logger.info(f"NER model predictions: tokens: {tokens_batch}, tags: {tags_batch}")
    good_preds = convert_prediction(tokens_batch, tags_batch)
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
