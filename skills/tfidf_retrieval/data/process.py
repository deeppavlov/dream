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


def get_vectorizer(vectorizer_dir):
    if 'new_vectorizer.pkl' not in os.listdir(os.getcwd()):
        urllib.request.urlretrieve(vectorizer_dir, "new_vectorizer.zip")
        with zipfile.ZipFile('new_vectorizer.zip', 'r') as zip_ref:
            zip_ref.extractall(os.getcwd())
    vectorizer = cPickle.load(open('new_vectorizer.pkl', 'rb'))
    return vectorizer


def get_dialogs(dialog_dir, custom_dialog_dir, full_dialog_dir, save_full=True):
    dialog_list = json.load(open(dialog_dir, 'r'))
    if os.path.isfile(custom_dialog_dir):
        custom_dialogs = json.load(open(custom_dialog_dir, 'r'))
        dialog_list = dialog_list + custom_dialogs
    if save_full:
        json.dump(dialog_list, open(full_dialog_dir, 'w'), indent=4)
    return dialog_list


def create_phraselist(dialog_list, donotknow_answers, todel_userphrases, banned_words):
    phrase_list = defaultdict(list)
    for dialog in dialog_list:
        utterances = dialog['utterances']
        for i in range(0, len(utterances) - 1, 2):
            human_phrase = utterances[i]
            bot_phrase = utterances[i + 1]
            no_wrongwords = all([banned_word not in bot_phrase for banned_word in banned_words])
            if bot_phrase not in donotknow_answers and human_phrase not in todel_userphrases and no_wrongwords:
                phrase_list[human_phrase].append(bot_phrase)
    logging.info('Phrase list created')
    for phrase in phrase_list.keys():
        phrase_list[phrase] = most_frequent(phrase_list[phrase])
    return phrase_list


vectorizer_dir = "http://lnsigo.mipt.ru/export/models/new_vectorizer.zip"
dialog_dir = "data/dialog_list.json"
custom_dialog_dir = "data/custom_dialog_list.json"
full_dialog_dir = "data/full_dialog_list.json"
donotknow_answers = ["I really do not know what to answer.",
                     "Sorry, probably, I didn't get what you mean.",
                     "I didn't get it. Sorry.",
                     "Let's talk about something else.",
                     "I'm newborn socialbot, so I can't do so much. For example I can answer for any question.",
                     "I'm really sorry but i'm a socialbot, and I cannot do some Alexa things.",
                     "I didn’t catch that.",
                     "I didn’t get that."]
todel_userphrases = ['yes']
banned_words = ['Benjamin']
vectorizer = get_vectorizer(vectorizer_dir=vectorizer_dir)
dialog_list = get_dialogs(dialog_dir=dialog_dir, custom_dialog_dir=custom_dialog_dir,
                          full_dialog_dir=full_dialog_dir)
phrase_list = create_phraselist(dialog_list=dialog_list, donotknow_answers=donotknow_answers,
                                todel_userphrases=todel_userphrases, banned_words=banned_words)


def check(human_phrase, vectorizer=vectorizer, phrase_list=phrase_list, top_best=2):
    human_phrases = list(phrase_list.keys())
    vectorized_phrases = vectorizer.transform(human_phrases)
    assert vectorized_phrases.shape[0] > 0
    transformed_phrase = vectorizer.transform([human_phrase.lower()])
    multiply_result = (transformed_phrase * vectorized_phrases.transpose())
    assert multiply_result.shape[0] > 0
    sorted_data = multiply_result.data.argsort()[::-1]
    # logging.info(sorted_data.shape)
    if sorted_data.shape[0] == 0:
        return [("I really do not know what to answer.", 0)]
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
