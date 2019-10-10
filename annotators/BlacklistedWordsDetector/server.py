#!/usr/bin/env python

import logging
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

tokenize_reg = re.compile(r"[\w']+|[^\w ]")

# get tokenized blacklisted words and phrases
blacklist_tokenized = [tokenize_reg.findall(line.strip().lower())
                       for line in open('./blacklists/profanity_blacklist.txt', 'r').readlines()]
blacklist = set([' '.join(phrase) for phrase in blacklist_tokenized])
max_n_gram = max([len(x) for x in blacklist_tokenized])


@app.route("/blacklisted_words", methods=['POST'])
def respond():
    """
    responses with  {'is_blacklisted': true} if at least one blacklisted phrase is in utterance
    """
    st_time = time.time()
    sentences = request.json['sentences']
    result = []
    for sentence in sentences:
        tokens = tokenize_reg.findall(sentence)
        unigrams = tokens[:]
        # as we have phrases in blacklist we should extract bigrams too
        all_ngrams = set(unigrams)
        for n_gram_len in range(2, max_n_gram):
            ngrams = set([' '.join(tokens[i: i + n_gram_len]) for i in range(len(tokens) - n_gram_len + 1)])
            all_ngrams = all_ngrams | ngrams
        result += [{'is_blacklisted': len(all_ngrams & blacklist) > 0}]

    total_time = st_time - time.time()
    logger.info(f'blacklisted_words exec time: {total_time:.3f}s')
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
