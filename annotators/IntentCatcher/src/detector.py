#!/usr/bin/env python

import os
from itertools import chain

import json
from typing import List

import numpy as np

import tensorflow as tf
import tensorflow_hub as hub

from collections import defaultdict

USE_MODEL_PATH = os.environ.get('USE_MODEL_PATH', None)
if USE_MODEL_PATH is None:
    USE_MODEL_PATH = 'https://tfhub.dev/google/universal-sentence-encoder/1'

INTENT_MODEL_PATH = os.environ.get('INTENT_MODEL_PATH', None)
if INTENT_MODEL_PATH is None:
    INTENT_MODEL_PATH = '/data/models/linear_classifier_h0.h5'

INTENT_DATA_PATH = os.environ.get('INTENT_DATA_PATH', None)
if INTENT_DATA_PATH is None:
    INTENT_DATA_PATH = '/data/intent_data.json'

TFHUB_CACHE_DIR = os.environ.get('TFHUB_CACHE_DIR', None)
if TFHUB_CACHE_DIR is None:
    os.environ['TFHUB_CACHE_DIR'] = '/root/tfhub_cache'

os.environ['TF_XLA_FLAGS'] = '--tf_xla_cpu_global_jit'  # Don't know that is


class AbstractDetector:

    def __init__(self, logger):
        self.logger = logger

    def detect(self, utterances: List, sess):
        raise NotImplementedError("Detect method not implemented!")


class ClassifierDetector(AbstractDetector):
    """
    Linear intent classifier based on USE embeddings.
    Current configuration is one linear layer upon USE embedding.

    """

    def __init__(self, logger):
        super().__init__(logger)
        self.data = json.load(open(INTENT_DATA_PATH))
        if 'random' in self.data.keys():
            self.data.pop('random')
        self.intents = sorted(list(self.data.keys()))
        self.embedder = hub.Module(USE_MODEL_PATH)
        self.model = tf.keras.models.load_model(INTENT_MODEL_PATH)
        self.sentences = tf.compat.v1.placeholder(dtype=tf.string)
        self.embedded_sentences = self.embedder(self.sentences)

    def detect(self, utterances : List, sess):
        self.logger.info(f"All utterances: {utterances}")
        len_sentences = [len(utt) for utt in utterances]
        tok_sentences = list(chain.from_iterable(utterances))
        embedded_sentences = sess.run(self.embedded_sentences, feed_dict={self.sentences: tok_sentences})

        predictions = self.model.predict(embedded_sentences)
        predictions_class = np.argmax(predictions, axis=1)
        prediction_confidence = np.max(predictions, axis=1)
        predictions = list(zip(predictions_class, prediction_confidence))

        i = 0
        detected_confidence = []
        for utt, l in zip(utterances, len_sentences):
            self.logger.info(f"Utterance: {utt}\nLength: {l}")
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


class MultilabelClassifierDetector(AbstractDetector):
    """
    Multilabel linear intent classifier based on USE embeddings.
    Current configuration is one linear layer upon USE embedding.

    """

    def __init__(self, logger):
        super().__init__(logger)
        self.data = json.load(open(INTENT_DATA_PATH))
        if 'random' in self.data:
            self.data.pop('random')
        self.intents = sorted(list(self.data.keys()))
        self.thresholds = np.array([self.data[intent] for intent in self.intents])
        self.embedder = hub.Module(USE_MODEL_PATH)
        self.model = tf.keras.models.load_model(INTENT_MODEL_PATH)
        self.sentences = tf.compat.v1.placeholder(dtype=tf.string)
        self.embedded_sentences = self.embedder(self.sentences)

    def glue_utterances_up(self, prediction):
        return list(chain.from_iterable(prediction))

    def detect(self, utterances : List, sess):
        self.logger.info(f"All utterances: {utterances}")
        len_sentences = [len(utt) for utt in utterances]
        tok_sentences = list(chain.from_iterable(utterances))
        embedded_sentences = sess.run(self.embedded_sentences, feed_dict={self.sentences: tok_sentences})

        predictions = self.model.predict(embedded_sentences)

        i = 0
        detected_confidence = []
        for utt, l in zip(utterances, len_sentences):
            self.logger.info(f"Utterance: {utt}\nLength: {l}")
            ans = {}
            prediction = [[(self.intents[j], p[j]) for j in np.argwhere(p > self.thresholds).reshape(-1)]
                          for p in predictions[i:i + l]]
            prediction = self.glue_utterances_up(prediction)
            confidences = defaultdict(float)
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


class MultilabelClassifierDetectorWithIntentHierarchy(AbstractDetector):
    """
    Multilabel linear intent classifier with intent priorities based on USE embeddings.
    Current configuration is one linear layer upon USE embedding.

    Intent priorities: choose intents from the last utterance in human sentence.
    """

    def __init__(self, logger):
        super().__init__(logger)
        self.data = json.load(open(INTENT_DATA_PATH))
        if 'random' in self.data:
            self.data.pop('random')
        self.intents = sorted(list(self.data.keys()))
        self.thresholds = [self.data[intent] for intent in self.intents]
        self.embedder = hub.Module(USE_MODEL_PATH)
        self.model = tf.keras.models.load_model(INTENT_MODEL_PATH)
        self.sentences = tf.compat.v1.placeholder(dtype=tf.string)
        self.embedded_sentences = self.embedder(self.sentences)
        self.intent_priorities = [
            'exit',
            'repeat',
            'cant_do',
            'dont_understand',
            'topic_switching'
        ]

    def glue_utterances_up(self, prediction):
        result = []
        for utt in prediction[::-1]:
            if len(utt) != 0:
                result = utt  # Get the last utterance with intent
        for target_intent in self.intent_priorities:  # Filter out intents by priority
            if any([intent == target_intent for intent, conf in result]) and len(result) > 1:
                result = [(intent, conf) for intent, conf in result if intent != target_intent]
        return result

    def detect(self, utterances : List, sess):
        self.logger.info(f"All utterances: {utterances}")
        len_sentences = [len(utt) for utt in utterances]
        tok_sentences = list(chain.from_iterable(utterances))
        embedded_sentences = sess.run(self.embedded_sentences, feed_dict={self.sentences: tok_sentences})

        predictions = self.model.predict(embedded_sentences)

        i = 0
        detected_confidence = []
        for utt, l in zip(utterances, len_sentences):
            self.logger.info(f"Utterance: {utt}\nLength: {l}")
            ans = {}
            prediction = [[(self.intents[j], p[j]) for j in np.argwhere(p > self.thresholds).reshape(-1)]
                          for p in predictions[i:i + l]]
            prediction = self.glue_utterances_up(prediction)
            confidences = defaultdict(float)
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
