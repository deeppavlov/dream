#!/usr/bin/env python

import os
import json
import itertools
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from sklearn.metrics import precision_recall_curve
from collections import OrderedDict, defaultdict
from utils import *

INTENT_PHRASES_PATH = './data/intent_phrases.json'
INTENT_DATA_PATH = './data/intent_data.json'

MODEL_PATH = os.environ.get('USE_MODEL_PATH', None)
if MODEL_PATH is None:
    MODEL_PATH = 'https://tfhub.dev/google/universal-sentence-encoder/1'

TFHUB_CACHE_DIR = os.environ.get('TFHUB_CACHE_DIR', None)
if TFHUB_CACHE_DIR is None:
    os.environ['TFHUB_CACHE_DIR'] = '../tfhub_model'

TRAIN_SIZE = 0.6
MIN_RECALL = 0.90
NUM_SAMPLING = 50

similarity_measure = cosine_similarity  # Choose sim measure


def main():
    model = hub.Module(MODEL_PATH)

    with open(INTENT_PHRASES_PATH, 'r') as fp:
        all_data = json.load(fp)
        intent_phrases = OrderedDict(all_data['intent_phrases'])
        random_phrases = all_data['random_phrases']

    intent_data = {}
    intents = intent_phrases.keys()

    with tf.compat.v1.Session() as sess:
        sess.run([tf.compat.v1.global_variables_initializer(), tf.compat.v1.tables_initializer()])

        intent_names = set(intent_phrases.keys())

        intent_preembedded = dict()
        for intent, sentences in intent_phrases.items():
            intent_preembedded[intent] = sentences
            intent_preembedded[intent] += [s + '.' for s in sentences] + [s + '!' for s in sentences]

        intent_embeddings_op = {intent: model([s.lower() for s in sentences])
                                for intent, sentences in intent_preembedded.items()}

        random_preembedded = random_phrases + [s + '.' for s in random_phrases] + [s + '!' for s in random_phrases]
        random_embeddings_op = model([s.lower() for s in random_preembedded])

        intent_embeddings = sess.run(intent_embeddings_op)
        random_embeddings = sess.run(random_embeddings_op)

        test_sentences = tf.compat.v1.placeholder(dtype=tf.float32, shape=[None, 512])  # Calculate scores
        intent_sentences = tf.compat.v1.placeholder(dtype=tf.float32, shape=[None, 512])
        score_op = similarity_measure(test_sentences, intent_sentences)

        for intent in intents:
            history = defaultdict(list)
            for t in range(NUM_SAMPLING):
                positive_sentences = intent_embeddings[intent]

                true_length = len(positive_sentences) // 3
                idx = np.random.choice(a=list(range(true_length)), size=int(TRAIN_SIZE * true_length))

                idx = np.concatenate((idx, [i + true_length for i in idx], [i + 2 * true_length for i in idx]))
                # Leave 60% to comparison, 40% to test

                train_positive = positive_sentences[idx].tolist()
                test_positive = positive_sentences[np.array(
                    list(set(range(len(positive_sentences))) - set(idx)))].tolist()
                negative_embeddings = [intent_embeddings[o_intent].tolist() for o_intent in (intent_names - {intent})]
                negative_embeddings += [random_embeddings]
                negative_embeddings = list(itertools.chain.from_iterable(negative_embeddings))
                labels = [1.0] * len(test_positive) + [0.0] * len(negative_embeddings)
                all_sentences = test_positive + negative_embeddings
                fd = {test_sentences: all_sentences, intent_sentences: train_positive}
                scores = sess.run(score_op, feed_dict=fd)

                # Filter scores and labels for identical utterances
                precision, recall, thresholds = precision_recall_curve(labels, scores)

                # filter precision/recall/thresholds by recall > MIN_RECALL
                # precision = precision[recall > MIN_RECALL]
                # thresholds = thresholds[recall > MIN_RECALL]
                # recall = recall[recall > MIN_RECALL]

                f1 = 2.0 * precision * recall / (precision + recall + 1e-10)
                threshold_i = np.argmax(f1)
                threshold = thresholds[threshold_i]
                predictions = [score >= threshold for score in scores]
                # probability of label given the prediction
                tp = np.mean([label for prediction, label in zip(predictions, labels) if prediction])
                fn = np.mean([label for prediction, label in zip(predictions, labels) if not prediction])

                history['tp'].append(tp)
                history['fn'].append(fn)
                history['precision'].append(precision[threshold_i])
                history['recall'].append(recall[threshold_i])
                history['f1'].append(f1[threshold_i])
                history['threshold'].append(threshold)

            intent_data[intent] = {
                'threshold' : float(np.mean(history['threshold'])),
                'tp' : float(np.mean(history['tp'])),
                'fn' : float(np.mean(history['fn'])),
                'embeddings' : intent_embeddings[intent].tolist(),
                'metrics' : {
                    'f1' : float(np.mean(history['f1'])),
                    'precision' : float(np.mean(history['precision'])),
                    'recall' : float(np.mean(history['recall']))
                }
            }
            # Lets print metrics
            print(f"Intent: {intent}\nMEAN + STD:")
            intent_mean_std = {
                'threshold' : {
                    'mean': float(np.mean(history['threshold'])),
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

    with open(INTENT_DATA_PATH, 'w') as fp:
        json.dump(intent_data, fp)


if __name__ == '__main__':
    main()
