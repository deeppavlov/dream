#!/usr/bin/env python

import os
import json
import argparse
from itertools import chain
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from sklearn.metrics import precision_recall_curve
from collections import OrderedDict, defaultdict
from utils import cosine_similarity, generate_phrases, train_test_split

parser = argparse.ArgumentParser()
parser.add_argument("phrases", help="phrases for embedding generation")
# Whereas to calc metrics or not (default value = True)
parser.add_argument("-t", "--add_thresholds", action="store_true")
parser.add_argument("-p", "--add_phrases", action="store_true")
args = parser.parse_args()

INTENT_PHRASES_PATH = args.phrases
INTENT_DATA_PATH = os.path.join(os.path.dirname(INTENT_PHRASES_PATH), 'intent_data.json')
print(f"Saving to: {INTENT_DATA_PATH}")

add_thresholds = args.add_thresholds
add_phrases = args.add_phrases

ANNOTATED_DATA_PATH = '../data/annotated_data.json'

MODEL_PATH = os.environ.get('USE_MODEL_PATH', None)
if MODEL_PATH is None:
    MODEL_PATH = 'https://tfhub.dev/google/universal-sentence-encoder/1'

TFHUB_CACHE_DIR = os.environ.get('TFHUB_CACHE_DIR', None)
if TFHUB_CACHE_DIR is None:
    os.environ['TFHUB_CACHE_DIR'] = '../tfhub_model'

TRAIN_SIZE = 0.5
MIN_PRECISION = 0.85
NUM_SAMPLING = 50

similarity_measure = cosine_similarity  # Choose sim measure


def print_intent_stats(intent_data, intent, history):
    print(f"Intent: {intent}\nMEAN + STD:")
    intent_mean_std = {
        'threshold' : {
            'mean': intent_data[intent]['threshold'],
            'std' : float(np.std(history['threshold']))
        },
        'tp' : {
            'mean' : float(np.mean(history['tp'])),
            'std' : float(np.std(history['tp']))
        },
        'fn' : {
            'mean' : float(np.mean(history['fn'])),
            'std' : float(np.std(history['fn']))
        },
        'metrics' : {
            'f1' : {
                'mean' : float(np.mean(history['f1'])),
                'std' : float(np.std(history['f1']))
            },
            'precision' : {
                'mean' : float(np.mean(history['precision'])),
                'std' : float(np.std(history['precision']))
            },
            'recall' : {
                'mean' : float(np.mean(history['recall'])),
                'std' : float(np.std(history['recall']))
            }
        }
    }
    print(json.dumps(intent_mean_std, sort_keys=True, indent=4, separators=(',', ': ')))
    print("\n" + "-" * 20 + "\n")


def calculate_metrics(intent_phrases, intent, labels, scores):
    # Filter scores and labels for identical utterances
    precision, recall, thresholds = precision_recall_curve(labels, scores)

    # filter precision/recall/thresholds by precision > MIN_PRECISION
    p_idx = np.argwhere(precision >= intent_phrases[intent]['min_precision']).reshape(-1)[0]
    precision = precision[p_idx:]
    recall = recall[p_idx:]
    thresholds = thresholds[p_idx:]

    f1 = 2.0 * precision * recall / (precision + recall + 1e-10)
    threshold_i = np.argmax(f1)
    threshold = thresholds[threshold_i]
    predictions = [score >= threshold for score in scores]
    # probability of label given the prediction
    tp = np.mean([label for prediction, label in zip(predictions, labels) if prediction])
    fn = np.mean([label for prediction, label in zip(predictions, labels) if not prediction])

    return precision[threshold_i], recall[threshold_i], f1[threshold_i], threshold, tp, fn


def main():
    model = hub.Module(MODEL_PATH)

    with open(INTENT_PHRASES_PATH, 'r') as fp:
        all_data = json.load(fp)
        intent_phrases = OrderedDict(all_data['intent_phrases'])
        random_phrases = all_data['random_phrases']

    with open(ANNOTATED_DATA_PATH, 'r') as fp:
        annotated_data = json.load(fp)

    intent_data = {}
    intents = list(intent_phrases.keys())

    with tf.compat.v1.Session() as sess:
        sess.run([tf.compat.v1.global_variables_initializer(), tf.compat.v1.tables_initializer()])

        intent_gen_phrases = dict()
        for intent, data in intent_phrases.items():
            phrases = generate_phrases(data['phrases'], data['punctuation'])
            if intent in annotated_data.keys():
                phrases += annotated_data[intent]
            # print(f"INTENT: {intent}\nNUM PHRASES:\n{len(phrases)}\n" + "-" * 50)
            intent_gen_phrases[intent] = {'phrases': phrases, 'punctuation': data['punctuation']}

        intent_embeddings_op = {intent: model(sentences['phrases'])
                                for intent, sentences in intent_gen_phrases.items()}

        random_preembedded = generate_phrases(random_phrases['phrases'], random_phrases['punctuation'])
        random_preembedded += annotated_data['random']
        random_embeddings_op = model(random_preembedded)

        intent_embeddings = sess.run(intent_embeddings_op)
        random_embeddings = sess.run(random_embeddings_op)

        if not add_phrases:
            for intent in intents:
                intent_data[intent] = {
                    'embeddings': intent_embeddings[intent].tolist(),
                    'punctuation': intent_gen_phrases[intent]['punctuation']
                }
            intent_data['random'] = {
                'embeddings' : random_embeddings.tolist(),
                'punctuation' : random_phrases['punctuation']
            }
        elif not add_thresholds:
            for intent in intents:
                intent_data[intent] = {
                    'embeddings': intent_embeddings[intent].tolist(),
                    'phrases': intent_gen_phrases[intent]['phrases'],
                    'punctuation': intent_gen_phrases[intent]['punctuation']
                }
        else:
            test_sentences = tf.compat.v1.placeholder(dtype=tf.float32, shape=[None, 512])  # Calculate scores
            intent_sentences = tf.compat.v1.placeholder(dtype=tf.float32, shape=[None, 512])
            score_op = similarity_measure(test_sentences, intent_sentences)
            for intent in intents:
                history = defaultdict(list)
                for t in range(NUM_SAMPLING):
                    positive_sentences = intent_embeddings[intent]

                    train_idx, test_idx = train_test_split(
                        intent_gen_phrases[intent],
                        len(intent_phrases[intent]['punctuation']),
                        TRAIN_SIZE
                    )

                    train_positive = positive_sentences[train_idx].tolist()
                    test_positive = positive_sentences[test_idx].tolist()
                    negative_embeddings = [intent_embeddings[o_intent].tolist()
                                           for o_intent in (set(intents) - {intent})]
                    negative_embeddings += [random_embeddings]
                    negative_embeddings = list(chain.from_iterable(negative_embeddings))
                    labels = [1.0] * len(test_positive) + [0.0] * len(negative_embeddings)
                    all_sentences = test_positive + negative_embeddings
                    fd = {test_sentences: all_sentences, intent_sentences: train_positive}
                    scores = sess.run(score_op, feed_dict=fd)

                    # Calculate metrics
                    precision, recall, f1, threshold, tp, fn = calculate_metrics(intent_phrases, intent, labels, scores)

                    history['tp'].append(tp)
                    history['fn'].append(fn)
                    history['precision'].append(precision)
                    history['recall'].append(recall)
                    history['f1'].append(f1)
                    history['threshold'].append(threshold)

                # Lets print metrics
                print_intent_stats(intent_data, intent, history)

                # Save data
                threshold = np.sum(np.array(history['f1']) * np.array(history['threshold']))
                threshold /= np.sum(history['f1'])
                intent_data[intent] = {
                    'threshold' : float(threshold),
                    'tp' : float(np.mean(history['tp'])),
                    'fn' : float(np.mean(history['fn'])),
                    'embeddings' : intent_embeddings[intent].tolist(),
                    'phrases' : intent_gen_phrases[intent]['phrases'],
                    'metrics' : {
                        'f1' : float(np.mean(history['f1'])),
                        'precision' : float(np.mean(history['precision'])),
                        'recall' : float(np.mean(history['recall']))
                    }
                }
        if not add_phrases:
            intent_data['random'] = {
                'embeddings' : random_embeddings.tolist(),
                'punctuation' : random_phrases['punctuation']
            }
        else:
            intent_data['random'] = {
                'embeddings' : random_embeddings.tolist(),
                'phrases' : random_preembedded,
                'punctuation' : random_phrases['punctuation']
            }

    with open(INTENT_DATA_PATH, 'w') as fp:
        json.dump(intent_data, fp)


if __name__ == '__main__':
    main()
