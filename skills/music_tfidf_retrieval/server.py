#!/usr/bin/env python
import logging
import time
import os
from data.process import check, create_phraselist, get_dialogs
from data.process import get_vectorizer, preprocess
from flask import Flask, request, jsonify
import sentry_sdk

sentry_sdk.init(os.getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

vectorizer_file = "../global_data/new_vectorizer_2.zip"
dialog_dir = "data/music_dialog_list.json"
full_dialog_dir = dialog_dir
custom_dialog_dir = "data/custom_dialog_list.json"

donotknow_answers = ["I really do not know what to answer.",
                     "Sorry, probably, I didn't get what you mean.",
                     "I didn't get it. Sorry.",
                     "Let's talk about something else.",
                     "I'm newborn socialbot, so I can't do so much. For example I can answer for any question.",
                     "I'm really sorry but i'm a socialbot, and I cannot do some Alexa things.",
                     "I didn’t catch that.",
                     "I didn’t get that."]
donotknow_answers = [preprocess(j) for j in donotknow_answers]
todel_userphrases = ['yes', 'wow', "let's talk about.", 'yeah', 'politics']
banned_words = ['Benjamin', 'misheard', 'cannot do this',
                "I didn't get your homeland .  Could you ,  please ,  repeat it . ", '#+#',
                "you are first. tell me something about positronic."]
vectorizer = get_vectorizer(vectorizer_file=vectorizer_file)
dialog_list = get_dialogs(dialog_dir=dialog_dir, custom_dialog_dir=custom_dialog_dir,
                          full_dialog_dir=full_dialog_dir)
bad_dialog_list = None
phrase_list = create_phraselist(dialog_list=dialog_list, donotknow_answers=donotknow_answers,
                                todel_userphrases=todel_userphrases, banned_words=banned_words,
                                bad_dialog_list=bad_dialog_list)
for user_phrase in todel_userphrases:
    if user_phrase in phrase_list:
        del phrase_list[user_phrase]
phrase_list["let's talk about."] = "i misheard you. what's it that you’d like to chat about?"


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    last_utterances = request.json['sentences']
    response = []
    for last_utterance in last_utterances:
        response = response + check(last_utterance, vectorizer=vectorizer, phrase_list=phrase_list)
    if not response:
        with sentry_sdk.push_scope() as scope:
            scope.set_extra('last_utterances', last_utterances)
            sentry_sdk.capture_message("No response in music_tfidf_retrieve")
        response = [["sorry", 0]]
    assert len(response[0]) == 2
    total_time = time.time() - st_time
    logger.info(f"music_tfidf exec time: {total_time:.3f}s")
    logger.info(response)
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
