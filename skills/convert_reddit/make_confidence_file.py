# ###################################################################
# for confidence was used confidence of convert_reddit
# ###################################################################

import argparse
import json
import pathlib
import re
import collections
import pickle

import numpy as np
import requests
import tqdm

parser = argparse.ArgumentParser()
parser.add_argument(
    "--url", help="skill_url", default="http://localhost:8029/convert_reddit",
)
# use data from skills/convert_reddit/tests/run_test.py
parser.add_argument(
    "-i", "--input", type=pathlib.Path, help="path to a json file", default="dialogs_file.json",
)
parser.add_argument(
    "-o", "--npy_file_path", type=pathlib.Path, help="path to npy file", default="confidences.npy",
)
parser.add_argument(
    "-c", "--cache_file_path", type=pathlib.Path, help="path to cache file", default="dialog_cache.pkl",
)
args = parser.parse_args()
data = json.load(args.input.open())

if args.cache_file_path.is_file():
    similar_requests = pickle.load(args.cache_file_path.open("rb"))
else:
    similar_requests = collections.defaultdict(list)
if isinstance(data, dict):
    data = [dialog[0] for dialog in list(data.values())]


def history_gen(dialog):
    for i in range(1, len(dialog) + 1):
        history = dialog[:i]
        yield history


spaces_pat = re.compile(r"\s+")
special_symb_pat = re.compile(r"[^A-Za-z0-9-!,.’?'\"’ ]")


def clear_text(text):
    return special_symb_pat.sub("", spaces_pat.sub(" ", text.lower().replace("\n", " "))).strip()


cached_counter = len(sum([list(set(set_conf)) for set_conf in similar_requests.values()], []))
glob_counter = 0
for dialog in tqdm.tqdm(data):
    dialog = [utt["text"] for utt in dialog["utterances"] if utt.get("active_skill", "") != "convert_reddit"]
    response = {}
    for utterances in history_gen(dialog):
        glob_counter += 1
        if glob_counter < cached_counter:
            continue
        res = requests.post(
            args.url, json={"utterances_histories": [utterances], "approximate_confidence_is_enabled": False},
        )
        assert str(res.status_code) == "200"
        res = res.json()
        for hyp in res:
            similar_requests[str(clear_text(utterances[-1]))].append(hyp[1])
    pickle.dump(similar_requests, args.cache_file_path.open("wb"))

confidences = sum([list(set(set_conf)) for set_conf in similar_requests.values()], [])
np.save(str(args.npy_file_path), confidences)
