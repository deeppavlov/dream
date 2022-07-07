#!/usr/bin/env python

import logging
import re
import time
from itertools import product
from os import getenv
from pathlib import Path
from typing import List, Set

import sentry_sdk
import spacy
from flask import Flask, request, jsonify
from spacy.tokens import Doc, Token


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


plural_to_singular_compiled_regexps = [
    (re.compile(r"(\w+)ies\b"), r"\g<1>y"),
    (re.compile(r"(\w+)(?<!s)s\b"), r"\g<1>"),
]


def lemmatize_noun_token(token: Token) -> Set[str]:
    variants = set()
    orig_token = str(token)
    for regex, repl in plural_to_singular_compiled_regexps:
        variant = regex.sub(repl, orig_token)
        if variant != orig_token:
            variants.add(variant)
            break
    if not variants or token.lemma_ != orig_token:
        variants.add(token.lemma_)
    return variants


def lemmatize(utterance: Doc) -> List[List[str]]:
    """
    Lemmatize nouns which are not subjects of the sentence
    Args:
        utterance: a sentence tokenized using Spacy model 'en_core_web_sm'
    Returns:
        List of maybe sentences. In each sentence all nouns except subject are lemmatized.
    """
    variants = {}
    utterance_lemmatized_unambiguously = []
    for i, token in enumerate(utterance):
        if token.pos_ == "NOUN" and token.dep_ != "nsubj":
            t_variants = lemmatize_noun_token(token)
            if len(t_variants) > 1:
                variants[i] = t_variants
                utterance_lemmatized_unambiguously.append(None)
            else:
                utterance_lemmatized_unambiguously.append(t_variants.pop())
        else:
            utterance_lemmatized_unambiguously.append(str(token))
    if variants:
        result = []
        for comb in product(*variants.values()):
            u = utterance_lemmatized_unambiguously.copy()
            for j, i in enumerate(variants.keys()):
                u[i] = comb[j]
            result.append(u)
    else:
        result = [utterance_lemmatized_unambiguously]
    return result


class Badlist:
    def __init__(self, path):
        """
        badlist object loads your favorite badlist from file
            https://www.freewebheaders.com/full-list-of-bad-words-banned-by-google/

        Args:
            path: Path object to badlist file, one badlisted phrase per line
        """
        self.name = path.stem
        self.badlist = set()
        with path.open() as f:
            for _phrase in f:
                phrase = _phrase.split(",")[0]
                tokenized = en_nlp(phrase.strip().lower())
                self.badlist.add(" ".join([str(token) for token in tokenized]))
                lemmatized_variants = lemmatize(tokenized)
                for lemmatized in lemmatized_variants:
                    self.badlist.add(" ".join(lemmatized))
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


def collect_ngrams(utterance: Doc, max_ngram: int):
    """
    Extracts all n-grams from utterance (n <= max_ngram)
    Args:
        utterance: spacy.tokens.Doc
        max_ngram: int
    Returns:
        set of all unique ngrams (ngram len <= self.max_ngram) in utterance
    """
    orig_words = [str(token) for token in utterance]
    lemmatized_variants = lemmatize(utterance)
    all_ngrams = set(orig_words) | set([t.lemma_ for t in utterance])
    for n_gram_len in range(2, max_ngram):
        orig_ngrams = set([" ".join(orig_words[i : i + n_gram_len]) for i in range(len(orig_words) - n_gram_len + 1)])
        all_ngrams |= orig_ngrams
    if lemmatized_variants[0] != orig_words:
        for lemmatized_words in lemmatized_variants:
            for n_gram_len in range(1, max_ngram):
                lemmatized_ngrams = set(
                    [
                        " ".join(lemmatized_words[i : i + n_gram_len])
                        for i in range(len(lemmatized_words) - n_gram_len + 1)
                    ]
                )
                all_ngrams |= lemmatized_ngrams
    return all_ngrams


en_nlp = spacy.load("en_core_web_sm", exclude=["senter", "ner"])

badlists_dir = Path("./badlists")
badlists_files = [f for f in badlists_dir.iterdir() if f.is_file()]

badlists = [Badlist(file) for file in badlists_files]
logger.info(f"badlisted_words initialized with following badlists: {badlists}")


def check_for_badlisted_phrases(sentences):
    result = []
    docs = list(en_nlp.pipe([s.lower() for s in sentences]))
    for doc in docs:
        ngrams = collect_ngrams(doc, max([bl.max_ngram for bl in badlists]))
        result += [{blist.name: blist.check_set_of_strings(ngrams) for blist in badlists}]
    return result


def get_result(request):
    st_time = time.time()
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
