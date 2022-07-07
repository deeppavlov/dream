import json
import re
import pandas as pd
import argparse
from copy import deepcopy
import requests

from common.ignore_lists import FALSE_POS_NPS_LIST, BAD_NPS_LIST


parser = argparse.ArgumentParser()

parser.add_argument("--mode", help="questions or facts", type=str)
args = parser.parse_args()
mode = args.mode

SERVICE_URL = "http://0.0.0.0:8016/nounphrases"

np_ignore_list = FALSE_POS_NPS_LIST + BAD_NPS_LIST

df = pd.read_csv(f"{mode}_with_topics.csv")
print(df.head())

df_dict = []

for i in range(df.shape[0]):
    df_dict.append({mode[:-1]: df.loc[i, mode[:-1]], "topic": df.loc[i, "topic"]})

batch_size = 100
all_topics = []

for i in range(int(len(df_dict) / batch_size) + 1):
    dialogs = [deepcopy({"utterances": [{"text": ""}]}) for _ in df_dict[i * batch_size : (i + 1) * batch_size]]

    for dialog, el in zip(dialogs, df_dict[i * batch_size : (i + 1) * batch_size]):
        dialog["utterances"][-1]["text"] = el[mode[:-1]]
    try:
        nounphrases = requests.request(url=SERVICE_URL, json={"dialogs": dialogs}, method="POST").json()
    except TypeError or ValueError or KeyError:
        print(dialogs)
        continue

    for el, np in zip(df_dict[i * batch_size : (i + 1) * batch_size], nounphrases):
        el["nounphrases"] = np

# extract unique noun phrases from dataet
unique_nps = []
spaces = re.compile(r"\s\s+")
ignore_np_res = []
for ignore_np in np_ignore_list:
    ignore_np_res.append(re.compile(r"\b%s\b" % ignore_np))

for sample in df_dict:
    for np in sample["nounphrases"]:
        for ignore_np in ignore_np_res:
            np = re.sub(spaces, " ", re.sub(ignore_np, "", np)).strip()
        if len(np) >= 3:
            unique_nps.append(np)
print(f"Total non-unique nounphrases: {len(unique_nps)}")
unique_nps = list(set(unique_nps))
print(f"Total unique nounphrases: {len(unique_nps)}")

np_to_fact_map = {}

for key in unique_nps:
    np_to_fact_map[key] = []

question_info = {}

total_id = 0

for sample in df_dict:
    question_info[total_id] = sample[mode[:-1]]
    total_id += 1

np_to_fact_map_res = []
for np in np_to_fact_map.keys():
    np = np.replace("(", "").replace(")", "")
    if len(np) < 1:
        np = "---"
    try:
        np_to_fact_map_res.append(re.compile(r"(\b%s\b)" % np))
    except Exception:
        np_to_fact_map_res.append(re.compile(r"(\b%s\b)" % "---"))


for sample_id in question_info.keys():
    for np, np_res in zip(np_to_fact_map.keys(), np_to_fact_map_res):
        if re.search(np_res, question_info[sample_id]):
            np_to_fact_map[np] += [sample_id]

bad_nps = []

for key in np_to_fact_map:
    if len(np_to_fact_map[key]) == 0:
        bad_nps.append(key)

for np in bad_nps:
    np_to_fact_map.pop(np)

print(f"Number of nounphrases: {len(np_to_fact_map)}")

with open(f"{mode}_map.json", "w") as f:
    json.dump(question_info, f, indent=2)

with open(f"nounphrases_{mode}_map.json", "w") as f:
    json.dump(np_to_fact_map, f, indent=2)
