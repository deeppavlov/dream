#!/usr/bin/env python

import logging
import re
import time
from os import getenv
from pathlib import Path
from typing import Set

import pymorphy2
import sentry_sdk
from flask import Flask, request, jsonify


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


lemmatizer = pymorphy2.MorphAnalyzer()
ANYTHING_EXCEPT_OF_LETTERS_RUSSIAN = re.compile(r"[^а-яА-Я йЙёЁ\-]+")
SPACES = re.compile(r"\s+")


def tokenize_sentence(sentence):
    if isinstance(sentence, list):
        # already tokenized
        return sentence
    else:
        sentence = ANYTHING_EXCEPT_OF_LETTERS_RUSSIAN.sub(" ", sentence)
        sentence = SPACES.sub(" ", sentence)
        return sentence.lower().split()


def lemmatize_token(token):
    return lemmatizer.parse(token)[0].normal_form


class Badlist:
    def __init__(self, path):
        """
        badlist object loads your favorite badlist from file

        Args:
            path: Path object to badlist file, one badlisted phrase per line
        """
        self.name = path.stem
        self.badlist = set()
        with path.open() as f:
            for line in f:
                token = line.strip().lower()
                self.badlist.add(token)
                self.badlist.add(lemmatize_token(token))

        self.max_ngram = max([len(x) for x in self.badlist])

    def check_set_of_strings(self, ngrams: Set[str]):
        """
        Checks if any bad listed phrase in a set of strings.
        Args:
            ngrams: set of str

        Returns:
            True if at least one badlisted phrase is in the set of str
        """
        badlists = ngrams & self.badlist
        if badlists:
            logger.info(f"badLIST {self.name}: {badlists}")
        return len(badlists) > 0

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


badlists_dir = Path("./badlists")
badlists_files = [f for f in badlists_dir.iterdir() if f.is_file()]

badlists = [Badlist(file) for file in badlists_files]
logger.info(f"badlisted_words initialized with following badlists: {badlists}")


def check_for_badlisted_phrases(sentences):
    result = []
    tokenized_sents = [tokenize_sentence(s) for s in sentences]
    tokenized_lemmatized_sents = [[lemmatize_token(token) for token in sent] for sent in tokenized_sents]
    unigrams = [set(tokens + lemmas) for tokens, lemmas in zip(tokenized_sents, tokenized_lemmatized_sents)]
    for sent_unigrams in unigrams:
        result += [{blist.name: blist.check_set_of_strings(sent_unigrams) for blist in badlists}]
    return result


def get_result(request):
    st_time = time.time()
    sentences = request.json.get("tokenized_sentences", [])

    if len(sentences) == 0:
        sentences = request.json["sentences"]
    result = check_for_badlisted_phrases(sentences)
    total_time = time.time() - st_time
    logger.info(f"badlisted_words exec time: {total_time:.3f}s")
    return result


@app.route("/badlisted_words", methods=["POST"])
def respond():
    """
    responses with  [{badlist_1_name: true}, ] if at least one badlisted phrase is in utterance
    """
    result = get_result(request)
    return jsonify(result)


@app.route("/badlisted_words_batch", methods=["POST"])
def respond_batch():
    """
    responses with [{"batch": [{badlist_1_name: true}, ]}]
    """
    result = get_result(request)
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
