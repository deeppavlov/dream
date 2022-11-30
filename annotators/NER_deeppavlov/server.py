import logging
import os
import re
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

nltk_stopwords_file = "nltk_stopwords.txt"
NLTK_STOPWORDS = set([line.strip() for line in open(nltk_stopwords_file, "r").readlines()])
BANNED_ENTITIES = re.compile(
    r"\b(okay|ok|name|ocean|hey|cool|corona|pop|rap|bo+"
    r"|hmph|oops|ouch|sh+|hush|whew|whoa|uhu|huh|wow|ya+y|yip+e+|yahoo|hurray"
    r"|[aeou]+[mhrw]+[aeou]*|[mhrw]+[aeou]+[mhrw]+|[mhrw]+|nowhere|nice|good"
    r"|somewhere|anywhere|honey)\b",
    re.IGNORECASE,
)

EVERYTHING_EXCEPT_LETTERS_DIGITALS_AND_SPACE = re.compile(r"[^a-zA-Z0-9 \-]")
DOUBLE_SPACES = re.compile(r"\s+")

with open("./google-english-no-swears.txt", "r") as f:
    UNIGRAMS = set(f.read().splitlines()[:500])


try:
    ner_model = build_model(config_name, download=True)
    r = "я видела ивана в москве"
    logger.info(f"Original: {r}. NER: {ner_model([r])}")
    logger.info("NER model is loaded.")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


def check_if_is_good_ent_text(ent_text):
    ent_text = EVERYTHING_EXCEPT_LETTERS_DIGITALS_AND_SPACE.sub(" ", ent_text)
    ent_text = DOUBLE_SPACES.sub(" ", ent_text).strip()
    is_not_stopword = ent_text not in NLTK_STOPWORDS and ent_text not in UNIGRAMS
    is_long_enough = len(ent_text) > 2
    is_not_banned = not re.match(BANNED_ENTITIES, ent_text)
    if is_not_stopword and is_not_banned and is_long_enough:
        return True
    return False


def convert_prediction(sents, pred_labels):
    entities = []
    for sent, tags in zip(sents, pred_labels):
        entities.append([])
        start = end = -1
        for i, (word, tag) in enumerate(zip(sent, tags)):
            if tag[0] == "B":
                if start != -1:
                    ent_text = " ".join(sent[start:end])
                    if check_if_is_good_ent_text(ent_text):
                        entities[-1].append(
                            {
                                "start_pos": start,
                                "end_pos": end,
                                "type": tags[start].split("-")[1],
                                "text": ent_text,
                                "confidence": 1,
                            }
                        )
                start = i
                end = i + 1
            elif tag[0] == "I":
                end = i + 1
            else:
                if start != -1:
                    ent_text = " ".join(sent[start:end])
                    if check_if_is_good_ent_text(ent_text):
                        entities[-1].append(
                            {
                                "start_pos": start,
                                "end_pos": end,
                                "type": tags[start].split("-")[1],
                                "text": ent_text,
                                "confidence": 1,
                            }
                        )
                    start = -1
        if start != -1:
            ent_text = " ".join(sent[start:end])
            if check_if_is_good_ent_text(ent_text):
                entities[-1].append(
                    {
                        "start_pos": start,
                        "end_pos": end,
                        "type": tags[start].split("-")[1],
                        "text": ent_text,
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
