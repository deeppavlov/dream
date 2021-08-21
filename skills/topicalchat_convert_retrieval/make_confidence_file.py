# ###################################################################
# for confidence was used confidence of convert_reddit
# ###################################################################

import argparse
import json
import pathlib

import numpy as np
import requests
import tqdm

parser = argparse.ArgumentParser()
parser.add_argument(
    "--url",
    help="skill_url",
    default="http://localhost:8060/respond",
)
# use data from skills/convert_reddit/tests/run_test.py
parser.add_argument(
    "-i",
    "--input",
    type=pathlib.Path,
    help="path to a json file",
    default="confidence_data.json",
)
parser.add_argument(
    "-o",
    "--npy_file_path",
    type=pathlib.Path,
    help="path to npy file",
    default="confidences.npy",
)
args = parser.parse_args()
data = json.load(args.input.open())


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
            json={
                "personality": [data["personality"]],
                "utterances_histories": [task["utterances_histories"]],
                "approximate_confidence_is_enabled": False,
                "topics": [
                    {
                        "text": [
                            "Art_Event",
                            "Celebrities",
                            "Entertainment",
                            "Fashion",
                            "Food_Drink",
                            "Games",
                            "Literature",
                            "Math",
                            "Movies_TV",
                            "Music",
                            "News",
                            "Other",
                            "Pets_Animals",
                            "Phatic",
                            "Politics",
                            "Psychology",
                            "Religion",
                            "SciTech",
                            "Sex_Profanity",
                            "Sports",
                            "Travel_Geo",
                            "Weather_Time",
                        ]
                    }
                ],
                "dialogact_topics": [
                    [
                        "Other",
                        "Interactive",
                        "Phatic",
                        "Entertainment_Movies",
                        "Science_and_Technology",
                        "Sports",
                        "Entertainment_Music",
                        "Entertainment_General",
                        "Politics",
                        "Entertainment_Books",
                    ]
                ],
            },
        )
        assert str(res.status_code) == "200"
        res = res.json()[0]
        for hyp in res:
            confidences.append(hyp[1])

np.save(str(args.npy_file_path), confidences)
