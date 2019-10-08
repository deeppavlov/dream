#!/usr/bin/env python

import tensorflow as tf
import numpy as np


def cosine_similarity(v, mat):
    mat_norm = tf.expand_dims(tf.math.sqrt(tf.math.reduce_sum(mat * mat, axis=1)),
                              0)  # (num_sent1, emb_dim) -> (1, num_sent1)
    v_norm = tf.expand_dims(tf.math.sqrt(tf.math.reduce_sum(v * v, axis=1)),
                            1)  # (num_sent2, emb_dim) -> (num_sent2, 1)
    return tf.math.reduce_max(v@(tf.transpose(mat)) / (v_norm@mat_norm), axis=1)  # (num_sent2)


def arccos_similarity(v, mat):
    return (1.0 - tf.math.acos(cosine_similarity(v, mat)) / np.pi)


def cosine_knn_similarity(v, mat):
    mat_norm = tf.expand_dims(tf.math.sqrt(tf.math.reduce_sum(mat * mat, axis=1)),
                              0)  # (num_sent1, emb_dim) -> (1, num_sent1)
    v_norm = tf.expand_dims(tf.math.sqrt(tf.math.reduce_sum(v * v, axis=1)),
                            1)  # (num_sent2, emb_dim) -> (num_sent2, 1)
    return tf.math.reduce_max(v@(tf.transpose(mat)) / (v_norm@mat_norm), axis=0)  # (num_sent1)


def arccos_knn_similarity(v, mat):
    return (1.0 - tf.math.acos(cosine_knn_similarity(v, mat)) / np.pi)
