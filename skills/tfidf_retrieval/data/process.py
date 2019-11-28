# -*- coding: utf-8 -*-
from collections import defaultdict
import os
import json
import _pickle as cPickle
import zipfile
import urllib.request
import logging


def most_frequent(List):
    return max(set(List), key=List.count)


urllib.request.urlretrieve(
    "http://lnsigo.mipt.ru/export/models/new_vectorizer.zip", "new_vectorizer.zip")
with zipfile.ZipFile('new_vectorizer.zip', 'r') as zip_ref:
    zip_ref.extractall(os.getcwd())

donotknow_answers = ["I really do not know what to answer.",
                     "Sorry, probably, I didn't get what you mean.",
                     "I didn't get it. Sorry.",
                     "Let's talk about something else.",
                     "I'm newborn socialbot, so I can't do so much. For example I can answer for any question.",
                     "I'm really sorry but i'm a socialbot, and I cannot do some Alexa things.",
                     "I didn’t catch that.",
                     "I didn’t get that."]

dialog_list = json.load(open('data/dialog_list.json', 'r'))
logging.info('List loaded')
phrase_list = defaultdict(list)
for dialog in dialog_list:
    for i in range(0, len(dialog) - 1, 2):
        human_phrase = dialog[i]
        bot_phrase = dialog[i + 1]
        if bot_phrase not in donotknow_answers and 'Benjamin' not in bot_phrase:
            phrase_list[human_phrase].append(bot_phrase)
logging.info('Phrase list created')
for phrase in phrase_list.keys():
    phrase_list[phrase] = most_frequent(phrase_list[phrase])

vectorizer = cPickle.load(open('new_vectorizer.pkl', 'rb'))

human_phrases = list(phrase_list.keys())
vectorized_phrases = vectorizer.transform(human_phrases)
assert vectorized_phrases.shape[0] > 0


def check(human_phrase, vectorizer=vectorizer, top_best=2):
    global phrase_list, vectorized_phrases, human_phrases
    assert len(human_phrases) > 0
    transformed_phrase = vectorizer.transform([human_phrase.lower()])
    # logging.info(str(transformed_phrase.shape))
    # logging.info(str(vectorized_phrases.shape))
    multiply_result = (transformed_phrase * vectorized_phrases.transpose())
    assert multiply_result.shape[0] > 0
    logging.info(str(multiply_result.shape))
    sorted_data = multiply_result.data.argsort()[::-1]
    # logging.info(sorted_data.shape)
    if sorted_data.shape[0] == 0:
        return [(donotknow_answers[0], 0)]
    best_inds = sorted_data[:top_best]
    assert len(best_inds) > 0
    ans = []
    for ind in best_inds:
        score = multiply_result.data[ind]
        if score < 0.6:
            score = score / 1.5
        index = multiply_result.indices[ind]
        bot_answer = phrase_list[human_phrases[index]]
        ans.append((bot_answer, score))
    return ans
