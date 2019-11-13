#!/usr/bin/env python

import os
import re
import itertools

import json
from typing import List

import numpy as np

import tensorflow as tf
import tensorflow_hub as hub

from collections import OrderedDict, defaultdict

from utils import *

MODEL_PATH = os.environ.get('USE_MODEL_PATH', None)
if MODEL_PATH is None:
    MODEL_PATH = 'https://tfhub.dev/google/universal-sentence-encoder/1'

INTENT_MODEL_PATH = '/data/classifier_data/models/linear_classifier.h5'
INTENT_DATA_PATH = '/data/classifier_data/intent_data.json'
INTENT_PHRASES_PATH = '/data/classifier_data/intent_phrases.json'

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
        if 'random' in self.data.keys():
            self.data.pop('random')
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

                logger_line = f"Intent: {intent}, threshold: {round(threshold, 3)} "
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


class USERegCombinedDetector(USESimpleDetector):
    def __init__(self, logger):
        super().__init__(logger)
        intent_phrases = json.load(open(INTENT_PHRASES_PATH))['intent_phrases']
        self.regexs = {intent: [re.compile(reg) for reg in v['phrases']]
                       for intent, v in intent_phrases.items()}

    def detect(self, utterances : List, sess):
        self.logger.disabled = True
        detected_confidence = []
        use_phrases = OrderedDict()
        for i, utt in enumerate(utterances):
            ans = {}
            any_detected = False
            for intent in self.intents:
                if any(any(reg.match(sent) for reg in self.regexs[intent]) for sent in utt):
                    ans[intent] = {'detected' : 1, 'confidence' : 1.0}
                    any_detected = True
                else:
                    ans[intent] = {'detected' : 0, 'confidence' : 0.0}
            if not any_detected:
                use_phrases[i] = utt
            detected_confidence.append(ans)

        use_input = list(use_phrases.values())  # USE detection
        if len(use_input):
            use_detected_confidence = super().detect(use_input, sess)
            for j, i in enumerate(use_phrases.keys()):
                detected_confidence[i] = use_detected_confidence[j]

        self.logger.disabled = False
        for dc, utt in zip(detected_confidence, utterances):  # Logging
            self.logger.info(f"Utterance : {utt}")
            for intent in self.intents:
                data = dc[intent]
                self.logger.info(f"Intent: {intent}, detect: {data['detected']}, confidence: {data['confidence']}")
        return detected_confidence


class ClassifierDetector(AbstractDetector):
    def __init__(self, logger):
        super().__init__(logger)
        self.data = json.load(open(INTENT_DATA_PATH))
        if 'random' in self.data.keys():
            self.data.pop('random')
        self.intents = sorted(list(self.data.keys()))
        self.embedder = hub.Module(MODEL_PATH)
        self.model = tf.keras.models.load_model(INTENT_MODEL_PATH)
        self.sentences = tf.compat.v1.placeholder(dtype=tf.string)
        self.embedded_sentences = self.embedder(self.sentences)

    def detect(self, utterances : List, sess):
        len_sentences = [len(utt) for utt in utterances]
        tok_sentences = list(itertools.chain.from_iterable(utterances))
        embedded_sentences = sess.run(self.embedded_sentences, feed_dict={self.sentences: tok_sentences})

        predictions = self.model.predict(embedded_sentences)
        predictions_class = np.argmax(predictions, axis=1)
        prediction_confidence = np.max(predictions, axis=1)
        predictions = list(zip(predictions_class, prediction_confidence))

        i = 0
        detected_confidence = []
        for utt, l in zip(utterances, len_sentences):
            self.logger.info(f"Utterance: {utt}")
            ans = {}
            prediction = [(self.intents[j], conf) for j, conf in predictions[i:i + l] if j < len(self.intents)]
            confidences = defaultdict(int)
            detected = {intent for intent, conf in prediction}
            for intent, conf in prediction:
                confidences[intent] = max(conf, confidences[intent])
            for intent in self.intents:
                logger_line = f"Intent: {intent}    "
                logger_line += f"prediction: {round(float(confidences[intent]), 3)}, detect: {int(intent in detected)}"
                self.logger.info(logger_line)

            ans = {intent: {'detected': int(intent in detected),
                            'confidence': float(confidences[intent])} for intent in self.intents}
            detected_confidence.append(ans)
            i += l
        return detected_confidence
