import logging
import os
import re
import time

import sentry_sdk
from flask import Flask, jsonify, request

from deeppavlov import build_model

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

config_name = os.getenv("CONFIG")

try:
    ner = build_model(config_name, download=True)
    ner(["what is the capital of russia"])
    logger.info("entity detection model is loaded.")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

nltk_stopwords_file = "nltk_stopwords.txt"
nltk_stopwords = [line.strip() for line in open(nltk_stopwords_file, "r").readlines()]
EVERYTHING_EXCEPT_LETTERS_DIGITALS_AND_SPACE = re.compile(r"[^a-zA-Z0-9 \-&*+]")
DOUBLE_SPACES = re.compile(r"\s+")


def get_result(request):
    st_time = time.time()
    last_utterances = request.json.get("last_utterances", [])
    logger.info(f"input (the last utterances): {last_utterances}")

    utterances_list = []
    utterances_nums = []
    for n, utterances in enumerate(last_utterances):
        for elem in utterances:
            if len(elem) > 0:
                utterances_list.append(elem.lower())
                utterances_nums.append(n)

    utt_entities_batch = [{} for _ in last_utterances]
    utt_entities = {}
    if utterances_list:
        entities_batch, tags_batch, positions_batch, entities_offsets_batch, probas_batch = ner(utterances_list)
        cur_num = 0
        for entities_list, tags_list, entities_offsets_list, num in zip(
            entities_batch, tags_batch, entities_offsets_batch, utterances_nums
        ):
            if num != cur_num:
                utt_entities_batch[cur_num] = utt_entities
                utt_entities = {}
                cur_num = num
            for entity, tag, offsets in zip(entities_list, tags_list, entities_offsets_list):
                if entity not in nltk_stopwords and len(entity) > 2:
                    entity = EVERYTHING_EXCEPT_LETTERS_DIGITALS_AND_SPACE.sub(" ", entity)
                    entity = DOUBLE_SPACES.sub(" ", entity).strip()
                    if "entities" in utt_entities:
                        utt_entities["entities"].append(entity)
                        utt_entities["labelled_entities"].append(
                            {"text": entity, "label": tag.lower(), "offsets": offsets}
                        )
                    else:
                        utt_entities["entities"] = [entity]
                        utt_entities["labelled_entities"] = [{"text": entity, "label": tag.lower(), "offsets": offsets}]
        if utt_entities:
            utt_entities_batch[cur_num] = utt_entities

    if not last_utterances:
        utt_entities_batch.append({})

    total_time = time.time() - st_time
    logger.info(f"entity detection exec time: {total_time: .3f}s")
    logger.info(f"entity_detection, input {last_utterances}, output {utt_entities_batch}")
    return utt_entities_batch


@app.route("/respond", methods=["POST"])
def respond():
    result = get_result(request)
    return jsonify(result)


@app.route("/respond_batch", methods=["POST"])
def respond_batch():
    result = get_result(request)
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8103)
