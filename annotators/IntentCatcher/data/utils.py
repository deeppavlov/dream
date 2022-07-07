#!/usr/bin/env python

import tensorflow as tf
import numpy as np
import random
import pandas as pd
from itertools import chain
from tqdm import tqdm
from xeger import Xeger
from sklearn.metrics import precision_recall_curve


def tb_accuracy(y_true, y_pred):
    y_true = tf.math.argmax(y_true, dimension=1)
    y_pred = tf.math.argmax(y_pred, dimension=1)
    return tf.keras.metrics.Accuracy()(y_true, y_pred)


def tb_f1(y_true, y_pred):
    precision = tf.keras.metrics.Precision()(y_true, y_pred)
    recall = tf.keras.metrics.Recall()(y_true, y_pred)
    return 2 * ((precision * recall) / (precision + recall + tf.keras.backend.epsilon()))


def multilabel_precision(y_true, y_pred):
    """
    Macro-precision, with thresholds defined by by argmax F1
    """
    values = list()
    for i in range(y_true.get_shape()[1]):
        pr, rec, thresholds = precision_recall_curve(y_true[:, i], y_pred[:, i])
        f1 = 2.0 * pr * rec / (pr + rec)
        values.append(pr[np.argmax(f1)])
    return np.mean(values)


def multilabel_recall(y_true, y_pred):
    """
    Macro-recall, with thresholds defined by argmax F1
    """
    values = list()
    for i in range(y_true.get_shape()[1]):
        pr, rec, thresholds = precision_recall_curve(y_true[:, i], y_pred[:, i])
        f1 = 2.0 * pr * rec / (pr + rec)
        values.append(rec[np.argmax(f1)])
    return np.mean(values)


def multilabel_f1(y_true, y_pred):
    """
    Macro-F1, with thresholds defined by argmax F1
    """
    values = list()
    for i in range(y_true.shape[1]):
        pr, rec, thresholds = precision_recall_curve(y_true[:, i], y_pred[:, i])
        f1 = 2.0 * pr * rec / (pr + rec)
        values.append(np.max(f1))
    return np.mean(values)


def calculate_metrics(intents_min_pr, y_true, y_pred):
    intent_data = dict()
    for i, intent in enumerate(intents_min_pr):
        pr, rec, thresholds = precision_recall_curve(y_true[:, i], y_pred[:, i])
        f1 = 2.0 * pr * rec / (pr + rec)
        indx = np.argwhere(pr > intents_min_pr[intent]).reshape(-1)
        # Argmax F1(threshold) where precision is greater than smth
        indx = indx[np.argmax(f1[indx])]
        intent_data[intent] = {
            "threshold": thresholds[indx],
            "precision": pr[indx],
            "recall": rec[indx],
            "f1": f1[indx],
        }
    return intent_data


def generate_phrases(template_re, punctuation, limit=2500):
    x = Xeger(limit=limit)
    phrases = []
    for regex in template_re:
        try:
            phrases += list({x.xeger(regex) for _ in range(limit)})
        except Exception as e:
            print(e)
            print(regex)
            raise e
    phrases = [phrases] + [[phrase + punct for phrase in phrases] for punct in punctuation]
    return list(chain.from_iterable(phrases))


def get_linear_classifier(intents, input_dim=512, dense_layers=1, use_metrics=True, multilabel=False):
    if multilabel:
        units = len(intents)
        activation = "sigmoid"
        metrics = [] if not use_metrics else ["binary_crossentropy"]
    else:
        units = len(intents) + 1
        activation = "softmax"
        metrics = (
            [] if not use_metrics else [tb_accuracy, tf.keras.metrics.Precision(), tf.keras.metrics.Recall(), tb_f1]
        )
    model = [
        tf.keras.layers.Dense(units=256, activation="relu", input_dim=input_dim if i == 0 else 256)
        for i in range(dense_layers)
    ]  # Hidden dense layers
    model += [
        tf.keras.layers.Dense(units=units, activation=activation, input_dim=input_dim if not len(model) else 256)
    ]  # Output layer
    model = tf.keras.Sequential(model)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(),
        loss="categorical_crossentropy" if not multilabel else "binary_crossentropy",
        metrics=metrics,
    )
    return model


def train_test_split(full_length, punct_num, train_size):
    original_length = full_length // (punct_num + 1)
    # Number of original phrases
    train_length = int(original_length * train_size)

    # Getting indexies
    train_idx = random.sample(list(range(original_length)), train_length)
    test_idx = list(set(range(original_length)) - set(train_idx))

    # Upsampling
    # train_length = max(train_length, 800)
    # test_length = max(test_length, 800)
    # train_idx = np.random.choice(train_idx, train_length)
    # test_idx = np.random.choice(test_idx, test_length)

    # With punctuation variants
    train_idx = list(chain.from_iterable([[i + original_length * p for i in train_idx] for p in range(punct_num + 1)]))
    test_idx = list(chain.from_iterable([[i + original_length * p for i in test_idx] for p in range(punct_num + 1)]))
    return train_idx, test_idx


def get_train_test_data(data, intents, random_phrases_embeddings, multilabel=False, train_size=0.8):
    train_data = {"X": [], "y": []}
    test_data = {"X": [], "y": []}
    num_classes = len(intents) + 1 if not multilabel else len(intents)
    for i, intent in enumerate(intents):
        train_idx, test_idx = train_test_split(
            len(data[intent]["embeddings"]), data[intent]["num_punctuation"], train_size=train_size
        )
        train = np.array(data[intent]["embeddings"])[train_idx]
        test = np.array(data[intent]["embeddings"])[test_idx]
        train_data["X"].append(train)
        train_data["y"].append([[1.0 if j == i else 0.0 for j in range(num_classes)] for _ in range(len(train))])
        test_data["X"].append(test)
        test_data["y"].append([[1.0 if j == i else 0.0 for j in range(num_classes)] for _ in range(len(test))])

    train_data["X"].append(random_phrases_embeddings)
    train_data["y"].append(
        [[1.0 if j == len(intents) else 0.0 for j in range(num_classes)] for _ in range(len(random_phrases_embeddings))]
    )

    train_data["X"] = np.concatenate(train_data["X"])
    test_data["X"] = np.concatenate(test_data["X"])
    train_data["y"] = np.concatenate(train_data["y"])
    test_data["y"] = np.concatenate(test_data["y"])
    return train_data, test_data


def get_train_data(data, intents, random_phrases_embeddings, multilabel=False):
    train_data = {"X": [], "y": []}
    num_classes = len(intents) + 1 if not multilabel else len(intents)
    for i, intent in enumerate(intents):
        train = np.array(data[intent]["embeddings"])
        train_data["X"].append(train)
        train_data["y"].append([[1.0 if j == i else 0.0 for j in range(num_classes)] for _ in range(len(train))])

    train_data["X"].append(random_phrases_embeddings)
    train_data["y"].append(
        [[1.0 if j == len(intents) else 0.0 for j in range(num_classes)] for _ in range(len(random_phrases_embeddings))]
    )

    train_data["X"] = np.concatenate(train_data["X"])
    train_data["y"] = np.concatenate(train_data["y"])
    return train_data


def score_model(
    data, intents, random_phrases_embeddings, samples=20, dense_layers=1, train_size=0.5, epochs=80, multilabel=False
):
    metrics = {intent: {"precision": [], "recall": [], "f1": [], "threshold": []} for intent in intents}
    intents_min_pr = {intent: v["min_precision"] for intent, v in data.items()}
    for _ in tqdm(range(samples)):
        model = get_linear_classifier(intents=intents, dense_layers=dense_layers, multilabel=multilabel)
        train_data, test_data = get_train_test_data(
            data, intents, random_phrases_embeddings, multilabel=multilabel, train_size=train_size
        )
        model.fit(x=train_data["X"], y=train_data["y"], epochs=epochs, verbose=0)

        current_metrics = calculate_metrics(intents_min_pr, test_data["y"], model.predict(test_data["X"]))
        for intent in current_metrics:
            for metric_name in current_metrics[intent]:
                metrics[intent][metric_name].append(current_metrics[intent][metric_name])
    for intent in intents:
        precision = (np.mean(metrics[intent]["precision"]), np.std(metrics[intent]["precision"]))
        recall = (np.mean(metrics[intent]["recall"]), np.std(metrics[intent]["recall"]))
        f1 = (np.mean(metrics[intent]["f1"]), np.std(metrics[intent]["f1"]))
        threshold = (np.mean(metrics[intent]["threshold"]), np.std(metrics[intent]["threshold"]))
        message = (
            f"\nIntent: {intent}\n"
            + f"PRECISION: {precision[0]}±{precision[1]}\n"
            + f"RECALL: {recall[0]}±{recall[1]}\n"
            + f"F1: {f1[0]}±{f1[1]}\n"
            + f"Threshold: {threshold[0]}±{threshold[1]}\n\n"
        )
        print(message)
    metrics = {intent: {metric: np.mean(metrics[intent][metric]) for metric in metrics[intent]} for intent in metrics}
    thresholds = {intent: float(np.mean(metrics[intent]["threshold"])) for intent in metrics}
    metrics = pd.DataFrame.from_dict(metrics)
    return metrics, thresholds
