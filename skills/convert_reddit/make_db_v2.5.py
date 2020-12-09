# %%

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

banned_responses = json.load((data_dir / "banned_responses_v3.json").open())
banned_phrases = json.load((data_dir / "banned_phrases.json").open())
banned_words = json.load((data_dir / "banned_words.json").open())
banned_words_for_questions = json.load((data_dir / "banned_words_for_questions.json").open())

banned_responses = [utils.clear_text(utter) for utter in banned_responses]

# %%

# main in/out-put files
banned_responses_file = data_dir / "banned_responses_v2.json"
db_file = work_dir / "convert_reddit" / "replies_v3.pkl"
output_db_file = work_dir / "convert_reddit" / "replies_v4.pkl"

# tmp data
chache_file = work_dir / "chache.json"
dropped_responses_file = work_dir / "dropped_responses.json"
log_file = work_dir / "logs.txt"

# curl -X POST "http://0.0.0.0:8011/sentseg" -H "accept: application/json" \
#  -H "Content-Type: application/json" \
#  -d "{\"sentences\": [\"hi how do you do today how are your deals\"]}"

response_encodings, responses = pickle.load(db_file.open("rb"))
# %%
responses[0]
# %%

dropped_indices = []
dropped_responses = []
for ind, cand_sent in enumerate(responses):
    cand = utils.clear_text(cand_sent).split()
    raw_cand = cand_sent.lower()
    # hello ban
    hello_flag = any([j in cand[:3] for j in ["hi", "hello"]])
    # banned_words ban
    banned_words_flag = any([j in cand for j in banned_words])
    banned_words_for_questions_flag = any([(j in cand and "?" in raw_cand) for j in banned_words_for_questions])

    # banned_phrases ban
    banned_phrases_flag = any([j in raw_cand for j in banned_phrases])

    # ban long words
    long_words_flag = any([len(j) > 30 for j in cand])

    if hello_flag or banned_words_flag or banned_words_for_questions_flag or banned_phrases_flag or long_words_flag:
        dropped_indices.append(ind)
        dropped_responses.append(cand_sent)
        continue
# %%
len(dropped_indices)
# %%
dropped_responses
# %%

# dropped_responses = responses

# save db
json.dump(dropped_responses, dropped_responses_file.open("tw"), indent=4)
pickle.dump([response_encodings, responses], output_db_file.open("wb"))


# %%
