import json
import os
import pickle

import pandas as pd
import tensorflow_hub as hub
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score
from sklearn.model_selection import train_test_split

from data2seq import Dial2seq, SequencePreprocessor
from midas_dataset import MidasDataset, MidasVectorizer


topical_sequencer = Dial2seq("data/topical_chat_annotated.json", 3)
daily_sequencer = Dial2seq("data/daily_dialogue_annotated.json", 3)
daily_seqs = daily_sequencer.transform()
print("Total number of sequences in the DailyDialog dataset is", len(daily_seqs))
topical_sequencer = Dial2seq("data/topical_chat_annotated.json", 3)
topical_seqs = topical_sequencer.transform()
print("Total number of sequences in the Topical Chat dataset is", len(topical_seqs))

preproc = SequencePreprocessor()
midas_dataset = preproc.transform(daily_seqs + topical_seqs)
len(midas_dataset)

train, val_test = train_test_split(midas_dataset, test_size=0.2, random_state=42)
val, test = train_test_split(val_test, test_size=0.5, random_state=42)

target_train = [sample["predict"] for sample in train]
target_val = [sample["predict"] for sample in val]
target_test = [sample["predict"] for sample in test]

target_train = pd.json_normalize(target_train)
target_val = pd.json_normalize(target_val)
target_test = pd.json_normalize(target_test)

print(set(target_val["midas"].value_counts().index.tolist()) - set(target_train["midas"].value_counts().index.tolist()))

print(
    set(target_test["midas"].value_counts().index.tolist()) - set(target_train["midas"].value_counts().index.tolist())
)

print(target_train["midas"].value_counts(normalize=True))

print(target_val["midas"].value_counts(normalize=True))

print(target_test["midas"].value_counts(normalize=True))

with open("data/annotated/midas_train.json", "w", encoding="utf-8") as f:
    json.dump(train, f, ensure_ascii=False, indent=2)

with open("data/annotated/midas_val.json", "w", encoding="utf-8") as f:
    json.dump(val, f, ensure_ascii=False, indent=2)

with open("data/annotated/midas_test.json", "w", encoding="utf-8") as f:
    json.dump(test, f, ensure_ascii=False, indent=2)

Midas2Id = {
    "appreciation": 0,
    "command": 1,
    "comment": 2,
    "complaint": 3,
    "dev_command": 4,
    "neg_answer": 5,
    "open_question_factual": 6,
    "open_question_opinion": 7,
    "opinion": 8,
    "other_answers": 9,
    "pos_answer": 10,
    "statement": 11,
    "yes_no_question": 12,
}
with open("data/annotated/midas_train.json", "r", encoding="utf8") as f:
    train = json.load(f)

with open("data/annotated/midas_val.json", "r", encoding="utf8") as f:
    val = json.load(f)

with open("data/annotated/midas_test.json", "r", encoding="utf8") as f:
    test = json.load(f)

print(len(train), len(val), len(test))


TFHUB_CACHE_DIR = os.environ.get("TFHUB_CACHE_DIR", None)
if TFHUB_CACHE_DIR is None:
    os.environ["TFHUB_CACHE_DIR"] = "/root/tfhub_cache"

USE_MODEL_PATH = os.environ.get("USE_MODEL_PATH", None)
if USE_MODEL_PATH is None:
    USE_MODEL_PATH = "https://tfhub.dev/google/universal-sentence-encoder/4"

encoder = hub.load(USE_MODEL_PATH)

midas_vectorizer = MidasVectorizer(
    text_vectorizer=encoder, midas2id=Midas2Id, context_len=3, embed_dim=512  # USE  # USE vector size
)
# check
# midas_vectorizer.context_vector(train[0]["previous_text"], train[0]["midas_vectors"])

train_dataloader = MidasDataset(data=train, vectorizer=midas_vectorizer, batch_size=len(train), shuffle=False)

val_dataloader = MidasDataset(data=val, vectorizer=midas_vectorizer, batch_size=len(val), shuffle=False)

test_dataloader = MidasDataset(data=test, vectorizer=midas_vectorizer, batch_size=len(test), shuffle=False)

for X_train, y_train in train_dataloader:
    break

for X_val, y_val in val_dataloader:
    break

for X_test, y_test in test_dataloader:
    break

print(X_train.shape, len(y_train), X_val.shape, len(y_val), X_test.shape, len(y_test))
print("Random Forest Training starts.")

MAX_DEPTH = 20

rfc_model = RandomForestClassifier(max_depth=MAX_DEPTH, random_state=42)

rfc_model.fit(X_train, y_train)

val_preds = rfc_model.predict(X_val)

print(accuracy_score(y_val, val_preds))

print(f1_score(y_val, val_preds, average="weighted"))

# conf_matrix = confusion_matrix(
#     [list(Midas2Id)[i] for i in y_val],
#     [list(Midas2Id)[i] for i in val_preds],
#     labels=list(Midas2Id))
#
# fig, ax = plt.subplots(figsize=(15, 15))
#
# ax.matshow(conf_matrix, cmap=plt.cm.Blues, alpha=0.3)
#
# for i in range(conf_matrix.shape[0]):
#     for j in range(conf_matrix.shape[1]):
#         ax.text(x=j, y=i,s=conf_matrix[i, j], va='center', ha='center', size='xx-large')
#
# plt.xlabel('Predictions', fontsize=14)
# plt.ylabel('Actuals', fontsize=18)
# plt.title('MIDAS Confusion Matrix', fontsize=18)
# plt.show()

# Store data (serialize)
with open(f"data/models/midas_predictor_rfc_depth{MAX_DEPTH}.pickle", "wb") as f:
    pickle.dump(rfc_model, f, protocol=pickle.HIGHEST_PROTOCOL)
