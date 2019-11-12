#!/usr/bin/env python

import os
import requests
import argparse
import json
from tqdm import tqdm
from sklearn.metrics import precision_score, recall_score, f1_score
import numpy as np
import pandas as pd
from utils import get_train_data, get_train_test_data, get_linear_classifier


MODEL_NAME = 'linear_classifier'
get_model = get_linear_classifier

TRAIN_SIZE = 0.8

# Optional: path to intent_data.json
parser = argparse.ArgumentParser()
parser.add_argument(
    '--data_path', help='path to intent_data.json, if not assigned - downloaded from share.ipavlov.mipt.ru')
args = parser.parse_args()

# Create metrics directory if not exists
if not os.path.exists('../../metrics/'):
    os.makedirs('../../metrics')


def score_model(data, samples=20, train_size=0.5, epochs=80):
    data, intents, random_phrases_embeddings = data
    metrics = {intent: {"precision" : [], "recall" : [], "f1" : []} for intent in intents}
    for _ in tqdm(range(samples)):
        model = get_linear_classifier(num_classes=len(intents) + 1)
        train_data, test_data = get_train_test_data(
            data,
            intents,
            random_phrases_embeddings,
            train_size=train_size
        )
        model.fit(
            x=train_data['X'],
            y=train_data['y'],
            epochs=epochs,
            verbose=0
        )
        y_true = np.argmax(test_data['y'], axis=1)
        y_pred = model.predict_classes(test_data['X'])
        precision = precision_score(y_true, y_pred, average=None)
        recall = recall_score(y_true, y_pred, average=None)
        f1 = f1_score(y_true, y_pred, average=None)
        for i, intent in enumerate(intents):
            metrics[intent]['precision'].append(precision[i])
            metrics[intent]['recall'].append(recall[i])
            metrics[intent]['f1'].append(f1[i])
    for intent in intents:
        precision = (np.mean(metrics[intent]['precision']), np.std(metrics[intent]['precision']))
        recall = (np.mean(metrics[intent]['recall']), np.std(metrics[intent]['recall']))
        f1 = (np.mean(metrics[intent]['f1']), np.std(metrics[intent]['f1']))
        message = f"Intent: {intent}\n\n" + \
            f"PRECISION: {precision[0]}±{precision[1]}\n\n" + \
            f"RECALL: {recall[0]}±{recall[1]}\n\n" + \
            f"F1: {f1[0]}±{f1[1]}\n\n"
        print(message)
    metrics = {intent: {metric: np.mean(metrics[intent][metric]) for metric in metrics[intent].keys()}
               for intent in metrics.keys()}
    metrics = pd.DataFrame.from_dict(metrics)
    return metrics


def main():
    if not args.data_path:
        print("Downloading data...")
        data = requests.get('http://files.deeppavlov.ai/alexaprize_data/intent_data.json').json()
        print("Downloading data...done")
    else:
        print(f'Loading data from: {args.data_path}')
        data = json.load(open(args.data_path))
    random_phrases = data.pop('random')
    random_phrases_embeddings = random_phrases['embeddings']
    intents = sorted(list(data.keys()))

    print("Scoring model...")
    metrics = score_model((data, intents, random_phrases_embeddings), samples=20, epochs=80)
    metrics.to_excel('../../metrics/' + MODEL_NAME + '_metrics.xlsx')
    print("METRICS:")
    print(metrics)

    train_data = get_train_data(data, intents, random_phrases_embeddings)
    model = get_linear_classifier(num_classes=len(intents) + 1, use_metrics=False)

    model.fit(
        x=train_data['X'],
        y=train_data['y'],
        epochs=80
    )
    model.save('./models/' + MODEL_NAME + '.h5')


if __name__ == '__main__':
    main()
