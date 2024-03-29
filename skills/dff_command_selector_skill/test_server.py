import requests
import os

import common.test_utils as test_utils


SERVICE_PORT = int(os.getenv("SERVICE_PORT"))
RANDOM_SEED = int(os.getenv("RANDOM_SEED", 2718))
URL = f"http://0.0.0.0:{SERVICE_PORT}/respond"
LANGUAGE = os.getenv("LANGUAGE", "EN")

FAKE_SERVER = os.getenv("FAKE", True)


def handler(requested_data, random_seed):
    hypothesis = requests.post(URL, json={**requested_data, "random_seed": random_seed}).json()
    return hypothesis


def run_test(handler):
    in_data, out_data = test_utils.get_dataset()
    for test_name in in_data:
        if LANGUAGE == "RU" and "RU" not in test_name:
            # if russian language, skip english tests
            continue
        elif LANGUAGE == "EN" and "EN" not in test_name:
            # if russian language, skip english tests
            continue
        if not FAKE_SERVER and "FAKE" in test_name:
            # skip fake server tests if the server is real
            continue

        hypothesis = handler(in_data[test_name], RANDOM_SEED)
        print(f"test name: {test_name}")
        is_equal_flag, msg = test_utils.compare_structs(out_data[test_name], hypothesis, ignored_keys=["id"])
        if msg and len(msg.split("`")) == 5:
            _, ground_truth_text, _, hypothesis_text, _ = msg.split("`")
            is_equal_flag, ratio = test_utils.compare_text(ground_truth_text, hypothesis_text, 0.80)
            if not is_equal_flag:
                msg = f"{msg} ratio = {ratio}"
        assert is_equal_flag, msg
        print("Success")


if __name__ == "__main__":
    run_test(handler)
