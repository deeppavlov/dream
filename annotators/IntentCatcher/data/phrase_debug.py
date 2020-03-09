#!/usr/bin/env python

import os
import json
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from utils import cosine_similarity_debug


INTENT_DATA_PATH = './data/intent_data.json'

MODEL_PATH = os.environ.get('USE_MODEL_PATH', None)
if MODEL_PATH is None:
    MODEL_PATH = 'https://tfhub.dev/google/universal-sentence-encoder/1'

TFHUB_CACHE_DIR = os.environ.get('TFHUB_CACHE_DIR', None)
if TFHUB_CACHE_DIR is None:
    os.environ['TFHUB_CACHE_DIR'] = '../tfhub_model'

PHRASES = [
    'Okay',
    'Okay, Alexa',
    'Bye, Alexa',
    'Alexa, bye',
    'Goodbye, Alexa',
    'Goodbye, bot',
    'Bot, goodbye',
    'Bye, bot',
    'Have a nice one',
    'Hello',
    'Hi',
    'Hello, bot',
    'Hello, Alexa',
    'Hi, bot',
    'Hi, Alexa',
    'Hey, Alexa',
    "Okay, have a good day!",
    "Have a good day, Alexa",
    "Okay, Alexa, have a good day"
]
INTENT = 'exit'


def main():
    model = hub.Module(MODEL_PATH)

    intent_data = json.load(open(INTENT_DATA_PATH))[INTENT]
    embedded_phrases = model(PHRASES)
    intent_phrases = np.array(intent_data['phrases'])
    threshold = intent_data['threshold']
    intent_embeddings = tf.constant(intent_data['embeddings'], dtype=tf.float32)
    sim = cosine_similarity_debug(embedded_phrases, intent_embeddings)
    with tf.compat.v1.Session() as sess:
        sess.run([tf.compat.v1.global_variables_initializer(), tf.compat.v1.tables_initializer()])
        values, similiarity_ids = sess.run(sim)

    for u in list(zip(PHRASES, intent_phrases[similiarity_ids], values, [threshold] * len(PHRASES))):
        print(u)


if __name__ == '__main__':
    main()
