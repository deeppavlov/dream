# -*- coding: utf-8 -*-
from collections import defaultdict
import os
import json
import _pickle as cPickle
import zipfile
import urllib.request
import logging
import tarfile
import pathlib
import time
import re

t = time.time()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(module)s %(lineno)d %(levelname)s : %(message)s",
    handlers=[
        logging.StreamHandler(),
        # logging.FileHandler('log.txt'),
    ],
)

logger = logging.getLogger(__name__)

TFIDF_BAD_FILTER = os.getenv("TFIDF_BAD_FILTER")
USE_COBOT = os.getenv("USE_TFIDF_COBOT")
USE_ASSESSMENT = os.getenv("USE_ASSESSMENT")


def most_frequent(List):
    return max(set(List), key=List.count)


spaces_pat = re.compile(r"\s+")
special_symb_pat = re.compile(r"[^A-Za-z ]")


def rm_spec_text_symls(text):
    return special_symb_pat.sub("", spaces_pat.sub(" ", text.lower().replace("\n", " "))).strip()


def preprocess(phrase):
    # return phrase
    for sign in "!$%.,:;?":
        phrase = phrase.replace(sign, " " + sign + " ")
    return phrase


def get_vectorizer(vectorizer_file='new_vectorizer_2.zip'):
    cond1 = "new_vectorizer.pkl" not in os.listdir(os.getcwd())
    cond2 = os.path.exists('new_vectorizer.pkl') and os.path.getsize('new_vectorizer.pkl') < 8412928
    if cond1 or cond2:
        with zipfile.ZipFile(vectorizer_file, "r") as zip_ref:
            zip_ref.extractall(os.getcwd())
    vectorizer = cPickle.load(open("new_vectorizer.pkl", "rb"))
    return vectorizer


def get_dataset(dataset_file, dataset_file_url):
    dataset_file = pathlib.Path(dataset_file)
    if not dataset_file.is_file():
        urllib.request.urlretrieve(dataset_file_url, "dataset.tar.gz")
        tar = tarfile.open("dataset.tar.gz", "r:gz")
        tar.extractall(str(dataset_file.parents[0]))
        tar.close()


def get_dialogs(dialog_dir, custom_dialog_dir, full_dialog_dir, save_full=True):
    dialog_list = json.load(open(dialog_dir, "r"))
    if custom_dialog_dir and os.path.isfile(custom_dialog_dir):
        custom_dialogs = json.load(open(custom_dialog_dir, "r"))
        dialog_list = dialog_list + custom_dialogs
    if save_full:
        json.dump(dialog_list, open(full_dialog_dir, "w"), indent=4)
    return dialog_list


def count(good, bad):
    return good / (good + bad + 0.001)


def create_phraselist(dialog_list, donotknow_answers, todel_userphrases, banned_words, bad_dialog_list=None):
    phrase_list = defaultdict(list)
    good_phrase_list = defaultdict(list)
    bad_phrase_list = defaultdict(list)
    good_total_count = 0
    bad_total_count = 0
    donotknow_answers = set(donotknow_answers)
    todel_userphrases = set(todel_userphrases)
    banned_words = set(banned_words)
    for dialog in dialog_list:
        utterances = dialog["utterances"]
        utterances = utterances[2:-2]  # drop "hi" and "goodbuy"
        for i in range(0, len(utterances) - 1, 2):
            human_phrase = preprocess(utterances[i])
            bot_phrase = preprocess(utterances[i + 1])
            no_wrongwords = all([banned_word.lower() not in bot_phrase.lower() for banned_word in banned_words])
            if bot_phrase not in donotknow_answers and human_phrase not in todel_userphrases and no_wrongwords:
                good_phrase_list[human_phrase].append(bot_phrase)
                good_total_count += 1
    if bad_dialog_list is not None:
        for dialog in bad_dialog_list:
            utterances = dialog["utterances"]
            for i in range(0, len(utterances) - 1, 2):
                human_phrase = utterances[i]
                bot_phrase = utterances[i + 1]
                no_wrongwords = all([banned_word not in bot_phrase for banned_word in banned_words])
                bad_phrase_list[human_phrase].append(bot_phrase)
                bad_total_count += 1
    logging.info("Phrase list created")
    for phrase in good_phrase_list.keys():
        candidate = most_frequent(good_phrase_list[phrase])
        good_count = good_phrase_list[phrase].count(candidate)
        bad_count = bad_phrase_list[phrase].count(candidate)
        if not bad_dialog_list or count(good_count, bad_count) > count(good_total_count, bad_total_count):
            phrase_list[phrase] = most_frequent(good_phrase_list[phrase])
    return phrase_list


right_chars = re.compile("[^A-Za-z0-9]+")


def tokenize(sentence):
    filtered_sentence = right_chars.sub(" ", sentence).split()
    filtered_sentence = [token for token in filtered_sentence if len(token) > 2]
    return set(filtered_sentence)


def is_available(candidate, utterances_history, threshold=0.6):
    candidate = tokenize(candidate)
    bot_history = [tokenize(utt) for utt in utterances_history[::-1][1::2]]
    return not ([True for utt in bot_history if len(candidate & utt) / (len(candidate) + 1) > threshold])


def check(
    human_phrase,
    vectorizer,
    vectorized_phrases,
    phrase_list,
    top_best=3,
    confidence_threshold=0.5,
    utterances_history=[],
):
    if len(rm_spec_text_symls(human_phrase).split()) < 2:
        return [("I really do not know what to answer.", 0)]
    human_phrase = preprocess(human_phrase)
    human_phrases = list(phrase_list.keys())
    assert vectorized_phrases.shape[0] > 0
    transformed_phrase = vectorizer.transform([human_phrase.lower()])
    multiply_result = transformed_phrase * vectorized_phrases.transpose()
    assert multiply_result.shape[0] > 0
    sorted_data = multiply_result.data.argsort()[::-1]
    # logging.info(sorted_data.shape)
    if sorted_data.shape[0] == 0:
        return [("I really do not know what to answer.", 0)]
    best_inds = sorted_data[:top_best]
    assert len(best_inds) > 0
    ans = []
    for ind in best_inds:
        index = multiply_result.indices[ind]
        bot_answer = phrase_list[human_phrases[index]]
        for sign in "!#$%&*+.,:;<>=?@[]^_{}|":
            bot_answer = bot_answer.replace(" " + sign, sign)
        bot_answer = bot_answer.replace("  ", " ").lower().strip()

        score = multiply_result.data[ind]
        score = (
            score / confidence_threshold * 0.5
            if score < confidence_threshold
            else (score - confidence_threshold) / (1 - confidence_threshold) * 0.5 + 0.5
        )
        if confidence_threshold != 0.5:  # if not testing
            score = score / 2 if score < 0.5 else score
        score = 0.95 if score > 0.95 else score
        score = score if is_available(bot_answer, utterances_history, 0.6) else 0.0
        ans.append((bot_answer, score))
    return sorted(ans, key=lambda x: -x[1])
