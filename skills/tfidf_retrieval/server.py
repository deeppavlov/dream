#!/usr/bin/env python
import logging
import time
from data.process import check, create_phraselist, get_dialogs
from data.process import get_vectorizer, preprocess
from flask import Flask, request, jsonify
import os
import string
import json
import sentry_sdk

TFIDF_BAD_FILTER = os.getenv('TFIDF_BAD_FILTER')
USE_COBOT = os.getenv('USE_TFIDF_COBOT')
USE_ASSESSMENT = os.getenv('USE_ASSESSMENT')

sentry_sdk.init(os.getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

vectorizer_file = "../global_data/new_vectorizer_2.zip"
dialog_dir = "../global_data/dialog_list.json"
full_dialog_dir = "data/full_dialog_list.json"  # We WRITE from this directory rather than read from it
custom_dialog_dir = "data/custom_dialog_list.json"

donotknow_answers = ["I really do not know what to answer.",
                     "Sorry, probably, I didn't get what you mean.",
                     "I didn't get it. Sorry.",
                     "Let's talk about something else.",
                     "I'm newborn socialbot, so I can't do so much. For example I can answer for any question.",
                     "I'm really sorry but i'm a socialbot, and I can't do some Alexa functions.",
                     "I didn’t catch that.",
                     "I didn’t get that.",
                     "superbowl", "super bowl"]
donotknow_answers = [preprocess(j) for j in donotknow_answers]
todel_userphrases = ['yes', 'wow', "let's talk about.", 'yeah', 'politics', 'superbowl', 'super bowl']
banned_words = ['Benjamin', 'misheard', 'cannot do this',
                "I didn't get your homeland .  Could you ,  please ,  repeat it . ", '#+#',
                "you are first. tell me something about positronic.",
                "you are first. tell me something about tronics."
                "sum up the internet", "your favorite movie",
                "without ever getting tired", "most ironic thing",
                "a fact about", "beg your pardon",
                "how stupid I am about", "a fruit machine in there",
                "might answer your question", "just to be negative",
                "newborn socialbot", "no_ answer", "i don't have an opinion on that",
                "super bowl", "let me ask you something", "i am glad to know you better",
                "Alexa, stop"]
vectorizer = get_vectorizer(vectorizer_file=vectorizer_file)
dialog_list = get_dialogs(dialog_dir=dialog_dir, custom_dialog_dir=custom_dialog_dir,
                          full_dialog_dir=full_dialog_dir)
if TFIDF_BAD_FILTER:
    bad_dialog_dir = "../global_data/bad_dialog_list.json"
    bad_dialog_list = get_dialogs(bad_dialog_dir, '', '', False)
else:
    bad_dialog_list = None
phrase_list = create_phraselist(dialog_list=dialog_list, donotknow_answers=donotknow_answers,
                                todel_userphrases=todel_userphrases, banned_words=banned_words,
                                bad_dialog_list=bad_dialog_list)
if USE_ASSESSMENT:
    goodbad_list = json.load(open('data/goodpoor.json', 'r'))[0]
    phrase_list.update(goodbad_list['good'])
    for key in goodbad_list['poor']:
        if key in phrase_list and goodbad_list['poor'][key] == phrase_list[key]:
            del phrase_list[key]
# gold_phrases = open('../global_data/gold_phrases.csv', 'r').readlines()[1:]
# gold_list = []
# for gold_phrase in gold_phrases:
#    if gold_phrase[0] == '"':
#        gold_phrase = gold_phrase[1:]
#    gold_phrase = gold_phrase.split('"\n')[0].split('" "')[0].lower()
#    if gold_phrase in phrase_list:
#        del phrase_list[gold_phrase]
for user_phrase in todel_userphrases:
    if user_phrase in phrase_list:
        del phrase_list[user_phrase]
# phrase_list["let's talk about."] = "i misheard you. what's it that you’d like to chat about?"
# phrase_list['politics'] = ' '.join(["my creators are still working on politics skill.",
#                                    "for now, i'm not able to perform such a discussion.",
#                                    "but i'll be glad to discuss movies with you.",
#                                    "what's your favorite movie?"])
vectorized_phrases = vectorizer.transform(list(phrase_list.keys()))


def nopunct(j):
    return ''.join([i for i in j if i not in string.punctuation])


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    last_utterances = request.json['sentences']
    response = []
    stopwords = [j.strip() for j in open('data/stopwords.txt', 'r').readlines()[1:]]
    for last_utterance in last_utterances:
        words = [j for j in nopunct(last_utterance).lower().split(' ') if len(j.strip()) > 0]
        if all([j in stopwords for j in words]):
            response = response + [['', 0]]
        else:
            response = response + check(last_utterance, vectorizer=vectorizer,
                                        vectorized_phrases=vectorized_phrases, phrase_list=phrase_list)
    if not response:
        with sentry_sdk.push_scope() as scope:
            scope.set_extra('last_utterances', last_utterances)
            sentry_sdk.capture_message("No response in tfidf_retrieve")
        response = [["sorry", 0]]
    for i in range(len(response)):
        if any([j in response[i][0].lower() for j in ['no_', 'unknown', 'interjection']]):
            response[i][0] = ''
    assert len(response[0]) == 2
    total_time = time.time() - st_time
    logger.info(f"Tfidf exec time: {total_time:.3f}s")
    logger.info(response)
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
