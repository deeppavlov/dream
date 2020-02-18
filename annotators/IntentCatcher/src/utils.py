#!/usr/bin/env python

import tensorflow as tf
import numpy as np
from itertools import chain
from xeger import Xeger


def cosine_similarity(v, mat):
    mat_norm = tf.expand_dims(tf.math.sqrt(tf.math.reduce_sum(mat * mat, axis=1)),
                              0)  # (num_sent1, emb_dim) -> (1, num_sent1)
    v_norm = tf.expand_dims(tf.math.sqrt(tf.math.reduce_sum(v * v, axis=1)),
                            1)  # (num_sent2, emb_dim) -> (num_sent2, 1)
    res = v@(tf.transpose(mat)) / (v_norm@mat_norm)
    return tf.math.reduce_max(res, axis=1)  # (num_sent2)


def arccos_similarity(v, mat):
    return (1.0 - tf.math.acos(cosine_similarity(v, mat)) / np.pi)


def generate_phrases(template_phrases_re, punctuation, limit=500):
    x = Xeger(limit=limit)
    phrases = []
    for regex in template_phrases_re:
        try:
            phrases += list({x.xeger(regex) for _ in range(limit)})
        except Exception as e:
            print(e)
            print(regex)
            raise e
    phrases = [phrases] + [[phrase + punct for phrase in phrases] for punct in punctuation]
    return list(chain.from_iterable(phrases))


def train_test_split(phrases, punct_num, train_size):
    original_length = len(phrases) // (punct_num + 1)
    train_idx = np.random.choice(range(original_length), int(train_size * original_length))
    train_idx = list(chain.from_iterable([[i + original_length * p for i in train_idx] for p in range(punct_num + 1)]))
    test_idx = list(set(range(len(phrases))) - set(train_idx))
    return train_idx, test_idx


def cosine_similarity_debug(v, mat):
    mat_norm = tf.expand_dims(tf.math.sqrt(tf.math.reduce_sum(mat * mat, axis=1)),
                              0)  # (num_sent1, emb_dim) -> (1, num_sent1)
    v_norm = tf.expand_dims(tf.math.sqrt(tf.math.reduce_sum(v * v, axis=1)),
                            1)  # (num_sent2, emb_dim) -> (num_sent2, 1)
    res = v@(tf.transpose(mat)) / (v_norm@mat_norm)
    return tf.math.reduce_max(res, axis=1), tf.math.argmax(res, axis=1)
