# -*- coding: utf-8 -*-
from collections import defaultdict
import os
import pandas as pd
import json
import _pickle as cPickle
import zipfile


def most_frequent(List):
    return max(set(List), key=List.count)


with zipfile.ZipFile('new_vectorizer.zip', 'r') as zip_ref:
    zip_ref.extractall(os.getcwd())
ratings = pd.read_csv('ratings.csv')
ratings = ratings[ratings['Rating'] >= 4]
conv_ids = ratings['Conversation ID']
conv_ids = set(list(conv_ids))

donotknow_answers = ["I really do not know what to answer.",
                     "Sorry, probably, I didn't get what you mean.",
                     "I didn't get it. Sorry.",
                     "Let's talk about something else.",
                     "I'm newborn socialbot, so I can't do so much. For example I can answer for any question.",
                     "I'm really sorry but i'm a socialbot, and I cannot do some Alexa things."]

dialogs = json.load(open('dialogs.3', 'r'))
dialog_list = list()
for dialog in dialogs:
    added = False
    utterances = dialog['utterances']
    for utterance in utterances:
        cond1 = 'attributes' in utterance
        cond2 = 'conversation_id' in utterance['attributes']
        cond3 = utterance['attributes']['conversation_id'] in conv_ids
        if cond1 and cond2 and cond3 and not added:
            added = True
            dialog_list.append(dialog)
cPickle.dump(dialog_list, open('dialog_list.pkl', 'wb'))

phrase_list = defaultdict(list)
for dialog in dialog_list:
    utterances = dialog['utterances']
    for i in range(0, len(utterances) - 1, 2):
        human_phrase = utterances[i]['text']
        bot_phrase = utterances[i + 1]['text']
        if bot_phrase not in donotknow_answers:
            phrase_list[human_phrase].append(bot_phrase)
for phrase in phrase_list.keys():
    phrase_list[phrase] = most_frequent(phrase_list[phrase])
vectorizer = cPickle.load(open('new_vectorizer.pkl', 'rb'))

vectorized_phrases = vectorizer.transform(list(phrase_list.keys()))


def check(human_phrase, vectorizer=vectorizer, top_best=1):
    global phrase_list, vectorized_phrases
    human_phrases = list(phrase_list.keys())
    transformed_phrase = vectorizer.transform([human_phrase])
    multiply_result = (transformed_phrase * vectorized_phrases.transpose())
    best_inds = multiply_result.data.argsort()[::-1][:top_best]
    ans = []
    for ind in best_inds:
        score = multiply_result.data[ind]
        bot_answer = phrase_list[human_phrases[ind]]
        ans.append((bot_answer, score))
    return ans
