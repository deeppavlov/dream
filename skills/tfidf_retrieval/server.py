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
stop_phrases_dir = "data/stop_phrases.txt"
todel_phrases = [j.strip() for j in open(stop_phrases_dir, 'r').readlines()]
todel_phrases = [preprocess(j) for j in todel_phrases]
todel_userphrases = ['yes', 'wow', "let's talk about.", 'yeah', 'politics', 'superbowl', 'super bowl']
vectorizer = get_vectorizer(vectorizer_file=vectorizer_file)
dialog_list = get_dialogs(dialog_dir=dialog_dir, custom_dialog_dir=custom_dialog_dir,
                          full_dialog_dir=full_dialog_dir)
if TFIDF_BAD_FILTER:
    bad_dialog_dir = "../global_data/bad_dialog_list.json"
    bad_dialog_list = get_dialogs(bad_dialog_dir, '', '', False)
else:
    bad_dialog_list = None
phrase_list = create_phraselist(dialog_list=dialog_list, todel_phrases=todel_phrases,
                                todel_userphrases=todel_userphrases,
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
        if any([j in preprocess(response[i][0]) for j in todel_phrases]):
            response[i] = ('', response[i][1])
    assert len(response[0]) == 2
    total_time = time.time() - st_time
    logger.info(f"Tfidf exec time: {total_time:.3f}s")
    logger.info(response)
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
