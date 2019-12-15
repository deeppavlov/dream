#!/usr/bin/env python

import logging
from pathlib import Path
import re
import time
from os import getenv

import sentry_sdk
from flask import Flask, request, jsonify

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
        self.tokenize_reg = re.compile(r"[\w']+|[^\w ]")
        self.blacklist_tokenized = [self.tokenize_reg.findall(line.strip().lower()) for line in path.open('r')]
        self.blacklist = set([' '.join(phrase) for phrase in self.blacklist_tokenized])
        self.max_ngram = max([len(x) for x in self.blacklist_tokenized])

    def _collect_ngrams(self, utterance):
        """
        Extracts all n-grams from utterance (n <= self.max_ngram)
        Args:
            utterance: str

        Returns:
            set of all unique ngrams (ngram len <= self.max_ngram) in utterance
        """
        tokens = self.tokenize_reg.findall(utterance)
        all_ngrams = set()
        for n_gram_len in range(1, self.max_ngram):
            ngrams = set([' '.join(tokens[i: i + n_gram_len]) for i in range(len(tokens) - n_gram_len + 1)])
            all_ngrams = all_ngrams | ngrams
        return all_ngrams

    def check_utterance(self, utterance):
        """
        Checks if any blacklisted phrase is in utterance
        Args:
            utterance: str

        Returns:
            True if at least one blacklisted phrase is in utterance else False
        """
        return len(self._collect_ngrams(utterance.lower()) & self.blacklist) > 0

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


blacklists_dir = Path('./blacklists')
blacklist_files = [f for f in blacklists_dir.iterdir() if f.is_file() and f.suffix == '.txt' and '_blacklist' in f.name]

blacklists = [Blacklist(file) for file in blacklist_files]
logger.info(f'blacklisted_words initialized with following blacklists: {blacklists}')


@app.route("/blacklisted_words", methods=['POST'])
def respond():
    """
    responses with  [{blacklist_1_name: true}, ] if at least one blacklisted phrase is in utterance
    """
    st_time = time.time()
    sentences = request.json['sentences']
    result = []
    for sentence in sentences:
        result += [{blist.name: blist.check_utterance(sentence) for blist in blacklists}]

    total_time = time.time() - st_time
    logger.info(f'blacklisted_words exec time: {total_time:.3f}s')
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
