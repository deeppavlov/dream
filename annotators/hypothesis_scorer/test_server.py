import json
import os

import numpy as np
import requests

SERVICE_PORT = int(os.getenv("SERVICE_PORT"))
URL = f"http://0.0.0.0:{SERVICE_PORT}/respond"


def get_dataset():
    dialogs_path = "tests/test_data.json"
    with open(dialogs_path) as f:
        dialogs = json.load(f)

    test_config = {"contexts": [], "hypotheses": []}
    dialog_ids = []
    for i, sample in enumerate(dialogs):
        for hyp in sample["hyp"]:
            test_config["contexts"] += [sample["context"]]
            test_config["hypotheses"] += [hyp]
            dialog_ids += [i]
    dialog_ids = np.array(dialog_ids)

    return dialogs, test_config, dialog_ids


def handler(contexts, hypotheses):
    return requests.post(URL, json={"contexts": contexts, "hypotheses": hypotheses}).json()


def run_test(handler):
    dialogs, test_config, dialog_ids = get_dataset()

    batch_responses = np.array(handler(**test_config))

    print(f"test name: {test_config}")

    for i, sample in enumerate(dialogs):
        curr_responses = batch_responses[dialog_ids == i]
        pred_best_hyp_id = np.argmax(curr_responses)

        assert sample["hyp"][pred_best_hyp_id], print(
            f"Current responses: {curr_responses}, pred best resp id: {pred_best_hyp_id}"
        )
    print("Success")


if __name__ == "__main__":
    run_test(handler)
