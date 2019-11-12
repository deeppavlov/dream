#!/usr/bin/env python

import tensorflow as tf
from itertools import chain
import numpy as np
from xeger import Xeger


def tb_accuracy(y_true, y_pred):
    y_true = tf.math.argmax(y_true, dimension=1)
    y_pred = tf.math.argmax(y_pred, dimension=1)
    return tf.keras.metrics.Accuracy()(y_true, y_pred)


def tb_f1(y_true, y_pred):
    precision = tf.keras.metrics.Precision()(y_true, y_pred)
    recall = tf.keras.metrics.Recall()(y_true, y_pred)
    return 2 * ((precision * recall) / (precision + recall + tf.keras.backend.epsilon()))


def get_linear_classifier(num_classes=8, input_dim=512, use_metrics=True):
    model = tf.keras.Sequential(
        [tf.keras.layers.Dense(units=num_classes, activation='softmax', input_dim=input_dim)]
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(),
        loss="categorical_crossentropy",
        metrics=[tb_accuracy, tf.keras.metrics.Precision(), tf.keras.metrics.Recall(), tb_f1] if use_metrics else []
    )
    return model


def train_test_split(phrases, punct_num, train_size):
    original_length = len(phrases) // (punct_num + 1)
    train_idx = np.random.choice(range(original_length), int(train_size * original_length))
    train_idx = list(chain.from_iterable([[i + original_length * p for i in train_idx] for p in range(punct_num + 1)]))
    test_idx = list(set(range(len(phrases))) - set(train_idx))
    return train_idx, test_idx


def get_train_test_data(data, intents, random_phrases_embeddings, train_size=0.8):
    train_data = {
        'X': [],
        'y': []
    }
    test_data = {
        'X': [],
        'y': []
    }
    num_classes = len(intents) + 1
    for i, intent in enumerate(intents):
        train_idx, test_idx = train_test_split(
            data[intent]['phrases'],
            len(data[intent]['punctuation']),
            train_size=train_size
        )
        train = np.array(data[intent]['embeddings'])[train_idx]
        test = np.array(data[intent]['embeddings'])[test_idx]
        train_data['X'].append(train)
        train_data['y'].append([[1.0 if j == i else 0.0 for j in range(num_classes)] for _ in range(len(train))])
        test_data['X'].append(test)
        test_data['y'].append([[1.0 if j == i else 0.0 for j in range(num_classes)] for _ in range(len(test))])

    train_data['X'].append(random_phrases_embeddings)
    train_data['y'].append([[1.0 if j == len(intents) else 0.0 for j in range(num_classes)]
                            for _ in range(len(random_phrases_embeddings))])

    train_data['X'] = np.concatenate(train_data['X'])
    test_data['X'] = np.concatenate(test_data['X'])
    train_data['y'] = np.concatenate(train_data['y'])
    test_data['y'] = np.concatenate(test_data['y'])
    return train_data, test_data


def get_train_data(data, intents, random_phrases_embeddings):
    train_data = {
        'X': [],
        'y': []
    }
    num_classes = len(intents) + 1
    for i, intent in enumerate(intents):
        train = np.array(data[intent]['embeddings'])
        train_data['X'].append(train)
        train_data['y'].append([[1.0 if j == i else 0.0 for j in range(num_classes)] for _ in range(len(train))])

    train_data['X'].append(random_phrases_embeddings)
    train_data['y'].append([[1.0 if j == num_classes - 1 else 0.0 for j in range(num_classes)]
                            for _ in range(len(random_phrases_embeddings))])

    train_data['X'] = np.concatenate(train_data['X'])
    train_data['y'] = np.concatenate(train_data['y'])
    return train_data


def generate_phrases(template_phrases_re, punctuation, limit=500):
    x = Xeger(limit=limit)
    phrases = []
    for regex in template_phrases_re:
        phrases += list({x.xeger(regex) for _ in range(limit)})
    phrases = [phrases] + [[phrase + punct for phrase in phrases] for punct in punctuation]
    return list(chain.from_iterable(phrases))
