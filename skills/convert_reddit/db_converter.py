# %%

import tqdm
import pickle
import pathlib
import json
import difflib
import logging

import requests

import utils


logger = logging.getLogger(__name__)


# %%
data_dir = pathlib.Path("data")
work_dir = pathlib.Path("tmp")

# main in/out-put files
banned_responses_file = data_dir / "banned_responses_v2.json"
db_file = work_dir / "convert_reddit" / "replies_v2.pkl"
output_db_file = work_dir / "convert_reddit" / "replies_v3.pkl"

# tmp data
chache_file = work_dir / "chache.json"
dropped_responses_file = work_dir / "dropped_responses.json"
log_file = work_dir / "logs.txt"

# curl -X POST "http://0.0.0.0:8011/sentseg" -H "accept: application/json" \
#  -H "Content-Type: application/json" \
#  -d "{\"sentences\": [\"hi how do you do today how are your deals\"]}"

response_encodings, responses = pickle.load(db_file.open("rb"))

# load cache
try:
    logger.warn("chache is loaded")
    reformatted_responses = json.load(chache_file.open())
except Exception:
    logger.warn("chache is not found")
    reformatted_responses = []

# rewrite by sentseg
url = "http://0.0.0.0:8011/sentseg"
for i, reply in tqdm.tqdm(enumerate(responses), total=len(responses)):
    if len(reformatted_responses) > i:
        continue
    if not (i % 100):
        json.dump(reformatted_responses, chache_file.open("tw"))
    rewrited_reply = requests.post(url, json={"sentences": [reply]}).json()[0]["punct_sent"]
    if i < 1000 and rewrited_reply != reply:
        log_file.open("ta").write(f"index: {i}\nreply: {reply}\nrewrited_reply: {rewrited_reply}\n\n")
    reformatted_responses.append(rewrited_reply)
json.dump(reformatted_responses, chache_file.open("tw"), indent=4)
assert len(responses) == len(reformatted_responses)

# ban replies
banned_responses = json.load(banned_responses_file.open())
banned_responses = [utils.clear_text(reply).split() for reply in banned_responses]
responses = [utils.clear_text(reply).split() for reply in responses]
banned_indices = []
for ind, reply in tqdm.tqdm(enumerate(responses), total=len(responses)):
    if [None for banned_reply in banned_responses if difflib.SequenceMatcher(None, banned_reply, reply).ratio() > 0.9]:
        banned_indices.append(ind)

# filter replies
response_encodings = [item for i, item in tqdm.tqdm(enumerate(response_encodings)) if i not in banned_indices]
dropped_responses = [item for i, item in tqdm.tqdm(enumerate(reformatted_responses)) if i in banned_indices]
reformatted_responses = [item for i, item in tqdm.tqdm(enumerate(reformatted_responses)) if i not in banned_indices]

# save db
json.dump(dropped_responses, dropped_responses_file.open("tw"), indent=4)
pickle.dump([response_encodings, reformatted_responses], output_db_file.open("wb"))
