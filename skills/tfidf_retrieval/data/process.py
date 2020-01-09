# -*- coding: utf-8 -*-
from collections import defaultdict
import os
import json
import _pickle as cPickle
import zipfile
import logging

TFIDF_BAD_FILTER = os.getenv('TFIDF_BAD_FILTER')
USE_COBOT = os.getenv('USE_TFIDF_COBOT')
USE_ASSESSMENT = os.getenv('USE_ASSESSMENT')


def most_frequent(List):
    return max(set(List), key=List.count)


def preprocess(phrase):
    for sign in '!$%&*.,:;<>=?@[]^_{}|':
        phrase = phrase.replace(sign, ' ' + sign + ' ')
    return phrase


def get_vectorizer(vectorizer_file='new_vectorizer_2.zip'):
    if "new_vectorizer.pkl" not in os.listdir(os.getcwd()):
        with zipfile.ZipFile(vectorizer_file, "r") as zip_ref:
            zip_ref.extractall(os.getcwd())
    vectorizer = cPickle.load(open("new_vectorizer.pkl", "rb"))
    return vectorizer


def get_dialogs(dialog_dir, custom_dialog_dir, full_dialog_dir, save_full=False):
    dialog_list = json.load(open(dialog_dir, 'r'))
    if os.path.isfile(custom_dialog_dir):
        custom_dialogs = json.load(open(custom_dialog_dir, 'r'))
        dialog_list = dialog_list + custom_dialogs
    if save_full:
        json.dump(dialog_list, open(full_dialog_dir, 'w'), indent=4)
    return dialog_list


def count(good, bad):
    return good / (good + bad + 0.001)


def create_phraselist(dialog_list, donotknow_answers, todel_userphrases, banned_words,
                      bad_dialog_list=None):
    phrase_list = defaultdict(list)
    good_phrase_list = defaultdict(list)
    bad_phrase_list = defaultdict(list)
    good_total_count = 0
    bad_total_count = 0
    for dialog in dialog_list:
        utterances = dialog['utterances']
        for i in range(0, len(utterances) - 1, 2):
            human_phrase = preprocess(utterances[i])
            bot_phrase = preprocess(utterances[i + 1])
            no_wrongwords = all([banned_word not in bot_phrase for banned_word in banned_words])
            if bot_phrase not in donotknow_answers and human_phrase not in todel_userphrases and no_wrongwords:
                good_phrase_list[human_phrase].append(bot_phrase)
                good_total_count += 1
    if bad_dialog_list is not None:
        for dialog in bad_dialog_list:
            utterances = dialog['utterances']
            for i in range(0, len(utterances) - 1, 2):
                human_phrase = utterances[i]
                bot_phrase = utterances[i + 1]
                no_wrongwords = all([banned_word not in bot_phrase for banned_word in banned_words])
                bad_phrase_list[human_phrase].append(bot_phrase)
                bad_total_count += 1
    logging.info('Phrase list created')
    for phrase in good_phrase_list.keys():
        candidate = most_frequent(good_phrase_list[phrase])
        good_count = good_phrase_list[phrase].count(candidate)
        bad_count = bad_phrase_list[phrase].count(candidate)
        if not TFIDF_BAD_FILTER or count(good_count, bad_count) > count(good_total_count, bad_total_count):
            phrase_list[phrase] = most_frequent(good_phrase_list[phrase])
    return phrase_list


def check(human_phrase, vectorizer, phrase_list, top_best=2):
    banned_phrases = ['where are you from?',
                      "hi, this is an alexa prize socialbot. yeah, let's chat! what do you want to talk about?",
                      "you are first. tell me something about positronic.",
                      "i'm made by amazon."]
    misheard_phrases = ["I misheard you",
                        "Could you repeat that, please?",
                        "Could you say that again, please?",
                        "I couldn't hear you",
                        "Sorry, I didn't catch that",
                        "What is it that you'd like to chat about?"]
    human_phrase = preprocess(human_phrase)
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
        score = min(score, 0.9)
        if score < 0.6:
            score = score / 1.5
        index = multiply_result.indices[ind]
        bot_answer = phrase_list[human_phrases[index]]
        for sign in '!#$%&*+.,:;<>=?@[]^_{}|':
            bot_answer = bot_answer.replace(' ' + sign, sign)
        bot_answer = bot_answer.replace('  ', ' ').lower().strip()
        assert "I didn't get your homeland." not in bot_answer
        cond1 = all([banned_phrase not in bot_answer for banned_phrase in banned_phrases + misheard_phrases])
        cond2 = len(human_phrase) >= 7 and 'alexa play' not in human_phrase.lower()
        if cond1 and cond2:
            ans.append((bot_answer, score))
        else:
            ans.append(("I really do not know what to answer.", 0))
    return ans
