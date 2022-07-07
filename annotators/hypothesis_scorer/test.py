import requests
import logging
import json
import numpy as np


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

URL = f"http://0.0.0.0:8110/batch_model"

dialogs_path = "test_data.json"
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


def main_test():
    batch_responses = requests.post(URL, json=test_config).json()[0]["batch"]
    batch_responses = np.array(batch_responses)

    for i, sample in enumerate(dialogs):
        curr_responses = batch_responses[dialog_ids == i]
        pred_best_hyp_id = np.argmax(curr_responses)

        assert sample["hyp"][pred_best_hyp_id], print(
            f"Current responses: {curr_responses}, pred best resp id: {pred_best_hyp_id}"
        )

    logger.info("Success!")


if __name__ == "__main__":
    main_test()
