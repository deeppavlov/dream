import json
import re
from itertools import chain

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import f1_score, roc_auc_score, accuracy_score
from sklearn.model_selection import StratifiedKFold
from transformers import EvalPrediction
from xeger import Xeger


TRANSFORMERS_MODEL_PATH = "sentence-transformers/distiluse-base-multilingual-cased-v2"
BATCH_SIZE = 4
MAX_LENGTH = 8


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


def get_regexp(intent_phrases_path):
    regexp = {
        intent: list(
            chain.from_iterable(
                [[phrase + "\\" + punct for phrase in data["phrases"]] for punct in data["punctuation"]]
            )
        )
        + [rf"^{pattern}[\.\?!]?$" for pattern in data.get("reg_phrases", [])]
        for intent, data in json.load(open(intent_phrases_path))["intent_phrases"].items()
    }
    regexp = {intent: [re.compile(phrase) for phrase in phrases] for intent, phrases in regexp.items()}
    return regexp


def create_label_map(labels):
    id2label = {idx: label for idx, label in enumerate(labels)}
    label2id = {label: idx for idx, label in enumerate(labels)}
    return id2label, label2id


def dump_dataset(intent_data, random_phrases, labels, train_path, valid_path):
    texts = []
    text_labels = []
    for intent in labels:
        texts += intent_data[intent]["generated_phrases"]
        text_labels += [intent] * len(intent_data[intent]["generated_phrases"])

    # random samples (do not belong to any class)
    texts += random_phrases
    text_labels += ["none"] * len(random_phrases)
    df = pd.DataFrame({"text": texts, "intents": text_labels})

    skf = StratifiedKFold(n_splits=2, shuffle=True, random_state=23)

    for train_index, test_index in skf.split(df["text"], df["intents"]):
        df_train = df.loc[train_index, :]
        df_train.reset_index(drop=True)
        df_train.to_csv(train_path, index=False)
        df_test = df.loc[test_index, :]
        df_test.reset_index(drop=True)
        df_test.to_csv(valid_path, index=False)
        break
    return


# source: https://jesusleal.io/2021/04/21/Longformer-multilabel-classification/
def multi_label_metrics(predictions, labels, threshold=0.5):
    # first, apply sigmoid on predictions which are of shape (batch_size, num_labels)
    sigmoid = torch.nn.Sigmoid()
    probs = sigmoid(torch.Tensor(predictions))
    # next, use threshold to turn them into integer predictions
    y_pred = np.zeros(probs.shape)
    y_pred[np.where(probs >= threshold)] = 1
    # finally, compute metrics
    y_true = labels
    f1_micro_average = f1_score(y_true=y_true, y_pred=y_pred, average="micro")
    roc_auc = roc_auc_score(y_true, y_pred, average="micro")
    accuracy = accuracy_score(y_true, y_pred)
    # return as dictionary
    metrics = {"f1": f1_micro_average, "roc_auc": roc_auc, "accuracy": accuracy}
    return metrics


def compute_metrics(p: EvalPrediction):
    preds = p.predictions[0] if isinstance(p.predictions, tuple) else p.predictions
    result = multi_label_metrics(predictions=preds, labels=p.label_ids)
    return result
