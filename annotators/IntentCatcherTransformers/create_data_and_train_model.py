#!/usr/bin/env python

import os
import json
import argparse
from collections import OrderedDict
from pathlib import Path

import numpy as np
import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer

from utils import generate_phrases, create_label_map, dump_dataset, compute_metrics


MODEL_NAME = "linear_classifier"
MULTILABEL = True
TRAIN_SIZE = 0.5
DENSE_LAYERS = 2
MODEL_NAME += "_h" + str(DENSE_LAYERS)
INTENT_DATA_PATH = "./intent_data_h" + str(DENSE_LAYERS) + ".json"

parser = argparse.ArgumentParser()
parser.add_argument(
    "--intent_phrases_path", help="file with phrases for embedding generation", default="intent_phrases.json"
)
parser.add_argument("--model_path", help="path where to save the model", default="./intents_model_v0")
parser.add_argument("--epochs", help="number of epochs to train model", default=7)
args = parser.parse_args()

TRANSFORMERS_MODEL_PATH = os.environ.get("TRANSFORMERS_MODEL_PATH", None)
if TRANSFORMERS_MODEL_PATH is None:
    TRANSFORMERS_MODEL_PATH = "distilbert-base-uncased"
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 8))
MAX_LENGTH = int(os.environ.get("MAX_LENGTH", 64))
MODEL_PATH = Path(f"data/").joinpath(args.model_path)
MODEL_PATH.mkdir(exist_ok=True)

tokenizer = AutoTokenizer.from_pretrained(TRANSFORMERS_MODEL_PATH)


def encode_dataset(df):
    global tokenizer, intents

    text_labels = np.array(df["intents"])
    # encode them
    encoding = tokenizer(df["text"], padding="max_length", truncation=True, max_length=MAX_LENGTH)

    # create numpy array of shape (batch_size, num_labels)
    labels_matrix = np.zeros((len(df["text"]), len(intents)))
    # fill numpy array
    for idx, label in enumerate(intents):
        labels_matrix[:, idx] = 1 * (text_labels == label)

    encoding["labels"] = labels_matrix.tolist()
    return encoding


def load(train_path, valid_path):
    dataset = load_dataset("csv", data_files={"train": [train_path], "valid": valid_path}, lineterminator="\n")
    encoded_dataset = dataset.map(encode_dataset, batched=True)
    encoded_dataset.set_format("torch")
    return encoded_dataset


with open(args.intent_phrases_path, "r") as fp:
    all_data = json.load(fp)
    intent_phrases = OrderedDict(all_data["intent_phrases"])
    random_phrases = all_data["random_phrases"]
    random_phrases = generate_phrases(random_phrases["phrases"], random_phrases["punctuation"])


intent_data = {}
intents = sorted(list(intent_phrases.keys()))
with open(MODEL_PATH.joinpath("intents.txt"), "w") as f:
    for intent in intents:
        f.write(intent + "\n")

print("Creating  data...")
print("Intent: number of original phrases")
id2label, label2id = create_label_map(intents)

classification_model = AutoModelForSequenceClassification.from_pretrained(
    TRANSFORMERS_MODEL_PATH,
    num_labels=len(intents),
    problem_type="multi_label_classification",
    id2label=id2label,
    label2id=label2id,
)
if torch.cuda.is_available():
    classification_model.to("cuda")
classification_model.train()
print("Loaded pre-trained model for fine-tuning")

for intent, data in intent_phrases.items():
    phrases = generate_phrases(data["phrases"], data["punctuation"])
    intent_data[intent] = {
        "generated_phrases": phrases,
        "num_punctuation": len(data["punctuation"]),
    }
    print(f"{intent}: {len(phrases)//len(data['punctuation'])}")

dump_dataset(
    intent_data,
    random_phrases,
    intents,
    train_path=MODEL_PATH.joinpath("intent_train.csv"),
    valid_path=MODEL_PATH.joinpath("intent_valid.csv"),
)
print("Dumped csv datasets")

encoded_dataset = load(
    train_path=MODEL_PATH.joinpath("intent_train.csv"), valid_path=MODEL_PATH.joinpath("intent_valid.csv")
)
print("Loaded encoded datasets")

args = TrainingArguments(
    "checkpoints",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    num_train_epochs=int(args.epochs),
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
)
trainer = Trainer(
    classification_model,
    args,
    train_dataset=encoded_dataset["train"],
    eval_dataset=encoded_dataset["valid"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)
print("Initial evaluation")
trainer.evaluate()
print("Training model...")
trainer.train()
print("Final evaluation")
trainer.evaluate()

print(f"Saving model to: `{str(MODEL_PATH)}`")
trainer.model.save_pretrained(str(MODEL_PATH))
