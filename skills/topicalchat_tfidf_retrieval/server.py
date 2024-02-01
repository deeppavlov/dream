#!/usr/bin/env python
import logging
import time
import os
import glob

from data.process import check, create_phraselist, get_dialogs
from data.process import get_vectorizer, preprocess
from flask import Flask, request, jsonify
import sentry_sdk

sentry_sdk.init(os.getenv("SENTRY_DSN"))

VECTORIZER_FILE = os.getenv("VECTORIZER_FILE", "/global_data/*vectorizer*.zip")
DIALOG_FILE = os.getenv("DIALOG_FILE", "/global_data/topicalchat_*_dialogs.json")
FULL_DIALOG_FILE = os.getenv("FULL_DIALOG_FILE", DIALOG_FILE)
CUSTOM_DIALOG_FILE = os.getenv("CUSTOM_DIALOG_FILE")
TOPIC_NAME = os.getenv("TOPIC_NAME", "no_name")
TEST_MODE = os.getenv("TEST_MODE")

CONFIDENCE_THRESHOLD = 0.5


def fuzzy_search_file(file_fuzzy_path):
    if file_fuzzy_path:
        cand_files = glob.glob(file_fuzzy_path)
        return cand_files[-1] if cand_files else None


VECTORIZER_FILE = fuzzy_search_file(VECTORIZER_FILE)
DIALOG_FILE = fuzzy_search_file(DIALOG_FILE)
FULL_DIALOG_FILE = fuzzy_search_file(FULL_DIALOG_FILE)
CUSTOM_DIALOG_FILE = fuzzy_search_file(CUSTOM_DIALOG_FILE)


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

donotknow_answers = [
    "I really do not know what to answer.",
    "Sorry, probably, I didn't get what you mean.",
    "I didn't get it. Sorry.",
    "Let's talk about something else.",
    "I'm newborn socialbot, so I can't do so much. For example I can answer for any question.",
    "I'm really sorry but i'm a socialbot, and I can't do some Alexa functions.",
    "I didn’t catch that.",
    "I didn’t get that.",
]
donotknow_answers = [preprocess(j) for j in donotknow_answers]
todel_userphrases = ["yes", "wow", "let's talk about.", "yeah", "politics", "hi", "no"]

# banned words are sensitive to tokenization in process.py:preprocess
banned_words = [
    "Benjamin",
    "misheard",
    "cannot do this",
    "I didn't get your homeland .  Could you ,  please ,  repeat it . ",
    "#+#",
    "tell me something about positronic",
    "she did for her role in Holocaust which earned her an Emmy",
    "this season is winding down and alex smith will be watching from home with his injury",
    "the theatrical genre of greek comedy can be described as a dramatic performance",
]
vectorizer = get_vectorizer(vectorizer_file=VECTORIZER_FILE)
dialog_list = get_dialogs(
    dialog_dir=DIALOG_FILE, custom_dialog_dir=CUSTOM_DIALOG_FILE, full_dialog_dir=FULL_DIALOG_FILE
)
bad_dialog_list = None
phrase_list = create_phraselist(
    dialog_list=dialog_list,
    donotknow_answers=donotknow_answers,
    todel_userphrases=todel_userphrases,
    banned_words=banned_words,
    bad_dialog_list=bad_dialog_list,
)
for user_phrase in todel_userphrases:
    if user_phrase in phrase_list:
        del phrase_list[user_phrase]

vectorized_phrases = vectorizer.transform(list(phrase_list.keys()))


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    last_utterances = request.json["sentences"]
    utterances_histories = request.json["utterances_histories"]
    response = []
    for last_utterance, utterances_history in zip(last_utterances, utterances_histories):
        response = response + check(
            last_utterance,
            vectorizer=vectorizer,
            vectorized_phrases=vectorized_phrases,
            phrase_list=phrase_list,
            confidence_threshold=CONFIDENCE_THRESHOLD,
            utterances_history=utterances_history,
        )
    if not response:
        with sentry_sdk.push_scope() as scope:
            scope.set_extra("last_utterances", last_utterances)
            sentry_sdk.capture_message(f"No response in topicalchat_{TOPIC_NAME}_tfidf_retrieva")
        response = [["sorry", 0]]
    assert len(response[0]) == 2
    total_time = time.time() - st_time
    logger.info(f"topicalchat_{TOPIC_NAME}_tfidf_retrieval exec time: {total_time:.3f}s")
    logger.info(response)
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
