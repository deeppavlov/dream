import argparse
import json
import pathlib

import numpy as np
import requests
import tqdm

# TGT_URL = os.getenv("TGT_URL", "http://localhost:8029/convert_reddit")
# N_REQUESTS = int(os.getenv("N_REQUESTS", 5))
# OUT_FILE = str(os.getenv("OUT_FILE", "confidences.npy"))

parser = argparse.ArgumentParser()
parser.add_argument(
    "--url",
    help="skill_url",
    default="http://localhost:8029/convert_reddit",
)
parser.add_argument(
    "--questions_json_file",
    type=pathlib.Path,
    help="path to a json file",
    default="tests/test_question_tasks.json",
)
parser.add_argument(
    "-o",
    "--npy_file_path",
    type=pathlib.Path,
    help="path to npy file",
    default="confidences.npy",
)
args = parser.parse_args()
data = json.load(args.questions_json_file.open())


def history_gen(dialogs):
    for dialog in dialogs:
        for i in range(1, len(dialog) + 1):
            history = dialog[:i]
            yield history


confidences = []
for task in tqdm.tqdm(data["tasks"]):
    response = {}
    for _ in range(1):
        res = requests.post(
            args.url,
            json={"personality": [data["personality"]], "utterances_histories": [task["utterances_histories"]]},
        ).json()[0]
        response[res[0]] = res[1]
    confidences.extend(response.values())

np.save(str(args.npy_file_path), confidences)
