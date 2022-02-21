#!/usr/bin/env python

import os
import json
import argparse
from collections import OrderedDict

import tensorflow as tf
import tensorflow_hub as hub
import tf_sentencepiece

from utils import *


# this is just to use library because without this import, m-use does not work
print(tf_sentencepiece.__file__)
config = tf.ConfigProto()
config.graph_options.rewrite_options.shape_optimization = 2
session = tf.Session(config=config)

MODEL_NAME = "linear_classifier"
MULTILABEL = True
TRAIN_SIZE = 0.5
DENSE_LAYERS = 3
MODEL_NAME += "_h" + str(DENSE_LAYERS)

parser = argparse.ArgumentParser()
parser.add_argument(
    "--intent_phrases_path", help="file with phrases for embedding generation", default="intent_phrases.json"
)
parser.add_argument("--model_path", help="path where to save the model", default="./models/" + MODEL_NAME + ".h5")
parser.add_argument(
    "--intent_data_path", help="path where to save theresholds", default="./intent_data_h" + str(DENSE_LAYERS) + ".json"
)
parser.add_argument("--epochs", help="number of epochs to train model", default=7)
# Whereas to calc metrics or not (default value = True)
args = parser.parse_args()
INTENT_DATA_PATH = args.intent_data_path

# Create metrics directory if not exists
if not os.path.exists("../metrics/"):
    os.makedirs("../metrics")

USE_MODEL_PATH = os.environ.get("USE_MODEL_PATH", None)
if USE_MODEL_PATH is None:
    USE_MODEL_PATH = "https://tfhub.dev/google/universal-sentence-encoder/1"

TFHUB_CACHE_DIR = os.environ.get("TFHUB_CACHE_DIR", None)
if TFHUB_CACHE_DIR is None:
    os.environ["TFHUB_CACHE_DIR"] = "../tfhub_model"


def main():
    use = hub.Module(USE_MODEL_PATH)

    with open(args.intent_phrases_path, "r") as fp:
        all_data = json.load(fp)
        intent_phrases = OrderedDict(all_data["intent_phrases"])
        random_phrases = all_data["random_phrases"]

    intent_data = {}
    intents = sorted(list(intent_phrases.keys()))
    print("Creating  data...")
    print("Intent: number of original phrases")
    with tf.compat.v1.Session() as sess:
        sess.run([tf.compat.v1.global_variables_initializer(), tf.compat.v1.tables_initializer()])

        for intent, data in intent_phrases.items():
            phrases = generate_phrases(data["phrases"], data["punctuation"])
            intent_data[intent] = {
                "generated_phrases": phrases,
                "num_punctuation": len(data["punctuation"]),
                "min_precision": data["min_precision"],
            }
            print(f"{intent}: {len(phrases)//len(data['punctuation'])}")

        intent_embeddings_op = {
            intent: use(sentences["generated_phrases"]) for intent, sentences in intent_data.items()
        }

        random_preembedded = generate_phrases(random_phrases["phrases"], random_phrases["punctuation"])
        random_embeddings_op = use(random_preembedded)

        intent_embeddings = sess.run(intent_embeddings_op)
        random_embeddings = sess.run(random_embeddings_op)

        for intent in intents:
            intent_data[intent] = {
                "embeddings": intent_embeddings[intent].tolist(),
                "min_precision": intent_data[intent]["min_precision"],
                "num_punctuation": intent_data[intent]["num_punctuation"],
            }

    print("Created!")

    random_embeddings = random_embeddings.tolist()

    print("Scoring model...")

    metrics, thresholds = score_model(
        intent_data,
        intents,
        random_embeddings,
        samples=20,
        dense_layers=DENSE_LAYERS,
        epochs=int(args.epochs),
        train_size=TRAIN_SIZE,
        multilabel=MULTILABEL,
    )

    metrics.to_csv("../metrics/" + MODEL_NAME + "_metrics.csv")
    print("METRICS:")
    print(metrics)

    print("Training model...")
    train_data = get_train_data(intent_data, intents, random_embeddings, multilabel=MULTILABEL)
    model = get_linear_classifier(intents, dense_layers=DENSE_LAYERS, use_metrics=False, multilabel=MULTILABEL)

    model.fit(x=train_data["X"], y=train_data["y"], epochs=int(args.epochs))
    print(f"Saving model to: {args.model_path}")
    model.save(args.model_path)
    print(f"Saving thresholds to: {INTENT_DATA_PATH}")
    json.dump(thresholds, open(INTENT_DATA_PATH, "w"))


if __name__ == "__main__":
    main()
