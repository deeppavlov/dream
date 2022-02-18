import json
import os

import numpy as np
import tensorflow_hub as hub
from catboost import CatBoostClassifier, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, accuracy_score

from label_encoder import LabelEncoder
from dataset import SkillDataset


os.environ['TFHUB_CACHE_DIR'] = './models/tf_cache'
module_url = "https://tfhub.dev/google/universal-sentence-encoder/4"
encoder = hub.load(module_url)
print("module %s loaded" % module_url)

# daily dialogs
with open('data/daily_labels.json', 'r', encoding="utf8") as f:
    daily_labels_map = json.load(f)

with open('data/daily_dataset.json', 'r', encoding="utf8") as f:
    daily = json.load(f)

#topicalchat
with open('data/topical_labels.json', 'r', encoding="utf8") as f:
    topical_labels_map = json.load(f)

with open('data/topical_dataset.json', 'r', encoding="utf8") as f:
    topical = json.load(f)

PARAMS = {
    'embed_dim': 512,
    'n_previous': 3
}


daily_dataset = SkillDataset(
    data=daily, vars2id=daily_labels_map,
    text_vectorizer=encoder,
    label_encoder=LabelEncoder(
        list(daily_labels_map['target_midas2id']),
        'midas'),
    shuffle=False, batch_size=len(daily), **PARAMS)

topical_dataset = SkillDataset(
    data=topical, vars2id=topical_labels_map,
    text_vectorizer=encoder,
    label_encoder=LabelEncoder(
        list(topical_labels_map['target_midas2id']),
        'midas'),
    shuffle=False, batch_size=len(topical), **PARAMS)

for X, y in daily_dataset:
    break
print(X.shape, y.shape)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

n_bins = len(daily_labels_map['target_midas2id'])
class_weights, _ = np.histogram(np.argmax(y_train, axis=-1), bins=n_bins, density=True)

cb_train = Pool(np.float32(X_train), label=np.argmax(y_train, axis=-1).tolist())
cb_eval = Pool(np.float32(X_test), label=np.argmax(y_test, axis=-1).tolist())

model_params = {
    'task_type': 'CPU',
    'iterations': 10,
    'learning_rate': 0.001,
    'depth': 3,
    'verbose': True,
    'loss_function': 'MultiClass',
    'eval_metric': 'Accuracy',
    # 'use_best_model': True,
    # 'class_weights': class_weights
}

fit_params = {
    # 'use_best_model': True,
    'early_stopping_rounds': 5,
    # 'eval_set': cb_eval,

}

model = CatBoostClassifier(**model_params)
model.fit(cb_train, **fit_params)

cb_pred = model.predict(cb_eval)
print("class = ", cb_pred.shape)

print(accuracy_score(np.argmax(y_test, axis=-1), cb_pred.squeeze()))
f1_score(np.argmax(y_test, axis=-1), cb_pred.squeeze(), average='weighted')

