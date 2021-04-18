import requests
import logging
import json
import numpy as np
import os


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


SERVICE_PORT = int(os.getenv("SERVICE_PORT"))
URL = f"http://0.0.0.0:{SERVICE_PORT}/batch_model"

dialogues_path = "test_data.json"
with open(dialogues_path) as f:
    dialogues = json.load(f)
test_config = {"dialogues": dialogues}


def main_test():
    batch_responses = requests.post(URL, json=test_config).json()
    best_idx_list = [np.argmax(x) for x in batch_responses[0]["batch"]]
    for d_idx, (best_idx, d) in enumerate(zip(best_idx_list, test_config["dialogues"])):
        assert d["hyp"][best_idx]["is_best"], d_idx

    logger.info("ResSel test passed")


if __name__ == "__main__":
    main_test()
