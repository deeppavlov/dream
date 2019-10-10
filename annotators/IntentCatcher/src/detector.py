#!/usr/bin/env python

import os
import itertools

import json
from typing import List

import tensorflow as tf
import tensorflow_hub as hub

from collections import OrderedDict

from src.utils import *

MODEL_PATH = os.environ.get('USE_MODEL_PATH', None)
if MODEL_PATH is None:
    MODEL_PATH = 'https://tfhub.dev/google/universal-sentence-encoder/1'

INTENT_DATA_PATH = 'src/data/intent_data.json'

TFHUB_CACHE_DIR = os.environ.get('TFHUB_CACHE_DIR', None)
if TFHUB_CACHE_DIR is None:
    os.environ['TFHUB_CACHE_DIR'] = '/root/tfhub_cache'
os.environ['TF_XLA_FLAGS'] = '--tf_xla_cpu_global_jit'  # Don't know that is


class AbstractDetector:

    def __init__(self, logger):
        self.logger = logger

    def detect(self, utterances: List, sess):
        raise NotImplementedError("Detect method not implemented!")


class USESimpleDetector(AbstractDetector):
    """
    Intent detector based on Universal Sentence Encoder.

    Takes in a list of utterances, embeddes each sentence within an utterance,
    and then compares it to a number of pre-defined intent phrases and
    takes the maximum sentence score within an utterance.

    """
    def __init__(self, logger):
        super().__init__(logger)
        self.data = json.load(open(INTENT_DATA_PATH))
        self.intents = sorted(list(self.data.keys()))
        self.embedder = hub.Module(MODEL_PATH)
        self.sentences = tf.compat.v1.placeholder(dtype=tf.string)
        self.embedded_sentences = self.embedder(self.sentences)
        embeddings = OrderedDict({intent : tf.constant(self.data[intent]['embeddings'], dtype=tf.float32)
                                  for intent in self.intents})
        self.similiarities = OrderedDict({intent: cosine_similarity(self.embedded_sentences, embeddings[intent])
                                          for intent in self.intents})  # Choose the metrics

    def detect(self, utterances: List, sess):
        len_sentences = [len(utt) for utt in utterances]
        tok_sentences = list(itertools.chain.from_iterable(utterances))
        similiarities = dict(zip(self.intents, sess.run(
            list(self.similiarities.values()), feed_dict={self.sentences: tok_sentences})))
        i = 0
        detected_confidence = []
        for utt, l in zip(utterances, len_sentences):
            self.logger.info(f"Utterance: {utt}")
            ans = {}
            for intent in self.intents:
                prediction = max(similiarities[intent][i:i + l])
                threshold = self.data[intent]['threshold']
                tp = self.data[intent]['tp']
                fn = self.data[intent]['fn']
                detect = int(prediction >= threshold)

                logger_line = f"Intent: {intent}, threhsold: {round(threshold, 3)} "
                logger_line += f"prediction: {round(float(prediction), 3)}, detect: {detect}"
                self.logger.info(logger_line)

                if detect:
                    conf = tp + (1 - tp) * (prediction - threshold) / (1 - threshold)
                else:
                    conf = fn * prediction / threshold
                ans[intent] = {'detected': detect, 'confidence': conf}
            detected_confidence.append(ans)
            i += l
        return detected_confidence


class USEKNNDetector(AbstractDetector):

    """
    Work in progress.
    """

    def __init__(self, logger):
        super().__init__(logger)
        self.data = json.load(open(INTENT_DATA_PATH))
        self.intents = sorted(list(self.data.keys()))
        self.embedder = hub.Module(MODEL_PATH)
        self.sentences = tf.compat.v1.placeholder(dtype=tf.string)
        self.embedded_sentences = self.embedder(self.sentences)
        self.similiarities = {intent: cosine_knn_similarity(self.embedded_sentences, self.data[intent]['embeddings'])
                              for intent in self.intents}  # Choose the metrics

    def detect(self, utterances: List, sess):
        for utt in utterances:
            self.logger.info(f"Utterance: {utt}")
        detected_confidence = []
        for utt in utterances:
            ans = {}
            count = {}
            conf = {}
            similiarities = sess.run(self.similiarities, feed_dict={self.sentences: utt})
            for intent in enumerate(self.intents):
                threshold = self.data[intent]['threshold']
                prediction = max(similiarities[intent])
                count[intent] = np.sum(similiarities[intent] > threshold)
                tp = self.data[intent]['tp']
                fn = self.data[intent]['fn']
                detect = count[intent] > 0
                if detect:
                    conf[intent] = tp + (1 - tp) * (prediction - threshold) / (1 - threshold)
                else:
                    conf[intent] = fn * prediction / threshold
                ans[intent] = {'detected': detect, 'confidence': conf}
            detected_confidence.append(ans)
        return detected_confidence
