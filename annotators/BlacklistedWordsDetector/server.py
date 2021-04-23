#!/usr/bin/env python

import logging
import time
from os import getenv
from pathlib import Path
from typing import List

import sentry_sdk
import spacy
from flask import Flask, request, jsonify
from spacy.tokens import Doc


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


class Blacklist:
    def __init__(self, path):
        """
        Blacklist object loads your favorite blacklist from text file
        Args:
            path: Path object to blacklist file, one blacklisted phrase per line
        """
        self.name = path.name.split('_blacklist')[0]
        self.blacklist = set()
        with path.open() as f:
            for phrase in f:
                tokenized = en_nlp(phrase.strip())
                self.blacklist.add(' '.join([str(token) for token in tokenized]))
                self.blacklist.add(' '.join(self._lemmatize(tokenized)))
        self.max_ngram = max([len(x) for x in self.blacklist])

    @staticmethod
    def _lemmatize(utterance: Doc) -> List[str]:
        """
        Lemmatize nouns which are not subjects of the sentence
        Args:
            utterance: a sentence tokenized using Spacy model ''en_core_web_sm'
        Returns:
            List of maybe lemmatized words
        """
        return [token.lemma_ if token.pos_ == "NOUN" and token.dep_ != "nsubj" else str(token) for token in utterance]

    def _collect_ngrams(self, utterance):
        """
        Extracts all n-grams from utterance (n <= self.max_ngram)
        Args:
            utterance: str

        Returns:
            set of all unique ngrams (ngram len <= self.max_ngram) in utterance
        """
        tokenized = en_nlp(utterance)
        orig_words = [str(token) for token in en_nlp(utterance)]
        lemmatized_words = self._lemmatize(tokenized)
        all_ngrams = set()
        for n_gram_len in range(1, self.max_ngram):
            orig_ngrams = set(
                [' '.join(orig_words[i: i + n_gram_len]) for i in range(len(orig_words) - n_gram_len + 1)])
            lemmatized_ngrams = set(
                [' '.join(lemmatized_words[i: i + n_gram_len]) for i in range(len(lemmatized_words) - n_gram_len + 1)]
            )
            all_ngrams = all_ngrams | orig_ngrams | lemmatized_ngrams
        return all_ngrams

    def check_utterance(self, utterance):
        """
        Checks if any blacklisted phrase is in utterance
        Args:
            utterance: str

        Returns:
            True if at least one blacklisted phrase is in utterance else False
        """
        blacklists = self._collect_ngrams(utterance.lower()) & self.blacklist
        if blacklists:
            logger.info(f"BLACKLIST {self.name}: {blacklists}")
        return len(blacklists) > 0

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


en_nlp = spacy.load('en_core_web_sm')

blacklists_dir = Path('./blacklists')
blacklist_files = [f for f in blacklists_dir.iterdir() if f.is_file() and f.suffix == '.txt' and '_blacklist' in f.name]

blacklists = [Blacklist(file) for file in blacklist_files]
logger.info(f'blacklisted_words initialized with following blacklists: {blacklists}')


def get_result(request):
    st_time = time.time()
    sentences = request.json['sentences']
    result = []
    for sentence in sentences:
        result += [{blist.name: blist.check_utterance(sentence) for blist in blacklists}]

    total_time = time.time() - st_time
    logger.info(f'blacklisted_words exec time: {total_time:.3f}s')
    return result


@app.route("/blacklisted_words", methods=['POST'])
def respond():
    """
    responses with  [{blacklist_1_name: true}, ] if at least one blacklisted phrase is in utterance
    """
    result = get_result(request)
    return jsonify(result)


@app.route("/blacklisted_words_batch", methods=['POST'])
def respond_batch():
    """
    responses with [{"batch": [{blacklist_1_name: true}, ]}]
    """
    result = get_result(request)
    return jsonify([{"batch": result}])


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
