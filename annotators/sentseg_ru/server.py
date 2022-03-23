import re
import logging
import time
from os import getenv

import sentry_sdk
import spacy
from deeppavlov import build_model
from flask import Flask, jsonify, request


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
config = getenv("CONFIG", "sentseg_ru.json")
PUNCTUATION = re.compile(r"[\.\?\!\,]+")
DOUBLE_SPACE = re.compile(r"\s+")


try:
    spacy_nlp = spacy.load("ru_core_news_sm")
    sentseg_model = build_model(config, download=True)
    m = sentseg_model(["привет как дела"])
except Exception as e:
    logger.exception("SentSeg Russian not loaded")
    sentry_sdk.capture_exception(e)
    raise e


def split_segments(sentence):
    segm = re.split(PUNCTUATION, sentence)
    segm = [sent.strip() for sent in segm if sent != ""]

    curr_sent = ""
    punct_occur = False
    segments = []

    for s in segm:
        if re.match(PUNCTUATION, s):
            punct_occur = True
            curr_sent += s
        elif punct_occur:
            segments.append(curr_sent)
            curr_sent = s
            punct_occur = False
        else:
            curr_sent += s
    segments.append(curr_sent)
    return segments


def add_punctuation(tokens, pred_labels):
    # sentseg_model = build_model(configs.ner.ner_ontonotes_bert_torch, download=True)
    #
    # sentseg_model(['привет как дела'])
    # >>> [[['привет', 'как', 'дела']], [['B-S', 'B-Q', 'O']]]
    tag2text = {"B-S": ".", "B-Q": "?", "O": "."}
    punctuation = tag2text[pred_labels[0]]
    sent = tokens[0]
    for word, tag in zip(tokens[1:], pred_labels[1:]):
        if tag != "O":
            sent += punctuation
            punctuation = tag2text[tag]
        sent += " " + word
    sent += punctuation
    logger.info(f"Punctuated: {sent}")
    return sent


def split_sentences(sentences):
    doc = spacy_nlp(sentences)
    return [sent.text for sent in doc.sents]


@app.route("/sentseg", methods=["POST"])
def respond():
    st_time = time.time()
    utterances = request.json["sentences"]
    utterances = [DOUBLE_SPACE.sub(" ", PUNCTUATION.sub(" ", uttr)) for uttr in utterances]
    ptokens = sentseg_model(utterances)
    punctuated = [add_punctuation(tokens, pred_labels) for tokens, pred_labels in zip(ptokens[0], ptokens[1])]
    segments = [split_sentences(utt) for utt in punctuated]

    sentseg_result = []
    for utt, segs in zip(punctuated, segments):
        sentseg_result += [{"punct_sent": utt, "segments": segs}]

    total_time = time.time() - st_time
    logger.info(f"sentseg exec time: {total_time:.3f}s")
    return jsonify(sentseg_result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
