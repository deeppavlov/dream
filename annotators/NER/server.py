import logging
import numpy as np
import re
import time
from copy import deepcopy
from os import getenv

import ner_model
import sentry_sdk
from flask import Flask, jsonify, request
from nltk.tokenize import word_tokenize

sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

ner = ner_model.load_model()
logger.info("ner model is loaded.")

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


def extract_good_entities(preds, sentences):
    good_preds = []
    for sent, entities_for_sent in zip(sentences, preds):
        good_entities_for_sent = []

        for ent in entities_for_sent:
            ent_text = ent["text"]
            ent_text = " ".join([ent_word[0].capitalize() + ent_word[1:] for ent_word in ent_text.split()])
            # remove everything except of letters, digitals, spaces and -
            ent_text = EVERYTHING_EXCEPT_LETTERS_DIGITALS_AND_SPACE.sub(" ", ent_text)
            ent_text = DOUBLE_SPACES.sub(" ", ent_text).strip()

            if ent_text == "alexa" and re.match("^alexa .+", sent):
                # skip alexa if alexa is a first word of uttr
                continue

            is_not_stopword = ent_text not in NLTK_STOPWORDS and ent_text not in UNIGRAMS
            is_long_enough = len(ent_text) > 2
            is_not_banned = not re.match(BANNED_ENTITIES, ent_text)
            if is_not_stopword and is_not_banned and is_long_enough:
                ent["text"] = ent_text
                good_entities_for_sent.append(deepcopy(ent))

        good_preds.append(good_entities_for_sent)
    return good_preds


def get_predictions_for_list_sentences(sentences):
    sents = [word_tokenize(sent.lower()) for sent in sentences]
    sents_upper = [word_tokenize(sent) for sent in sentences]
    preds = ner.predict(sents)
    for i in range(len(preds)):
        sent_upper = sents_upper[i]
        for j in range(len(preds[i])):
            ent_upper = " ".join(sent_upper[preds[i][j]["start_pos"] : preds[i][j]["end_pos"]])
            if ent_upper.lower() == preds[i][j]["text"]:
                preds[i][j]["text"] = ent_upper
    # each sample is a list of sentences of current utterance
    # so, preds is a list of length = number of sents in utterances
    # each element of preds is a list of entities.
    # EXAMPLE:
    # one sample = ["i have been in london and greece.", "my name is valentine and beatrice."]
    # preds = [[{'confidence': 1, 'end_pos': 5, 'start_pos': 4, 'text': 'london', 'type': 'LOC'},
    #           {'confidence': 1, 'end_pos': 7, 'start_pos': 6, 'text': 'greece', 'type': 'LOC'}],
    #          [{'confidence': 1, 'end_pos': 4, 'start_pos': 3, 'text': 'valentine', 'type': 'PER'},
    #           {'confidence': 1, 'end_pos': 6, 'start_pos': 5, 'text': 'beatrice', 'type': 'PER'}]]

    good_preds = extract_good_entities(preds, sentences)
    return good_preds


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

    good_preds = get_predictions_for_list_sentences(samples)
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
