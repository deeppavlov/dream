import requests
import os

import common.test_utils as test_utils


INTENT_RESPONSE_PHRASES_FNAME = os.getenv("INTENT_RESPONSE_PHRASES_FNAME", "intent_response_phrases.json")
SERVICE_PORT = int(os.getenv("SERVICE_PORT"))
RANDOM_SEED = int(os.getenv("RANDOM_SEED", 2718))
URL = f"http://0.0.0.0:{SERVICE_PORT}/respond"


def handler(requested_data, random_seed):
    hypothesis = requests.post(URL, json={**requested_data, "random_seed": random_seed}).json()
    return hypothesis


def run_test(handler):
    in_data, out_data = test_utils.get_dataset()
    for test_name in in_data:
        if "RU" in INTENT_RESPONSE_PHRASES_FNAME and "RU" not in test_name:
            # if russian language, skip english tests
            continue
        elif "RU" not in INTENT_RESPONSE_PHRASES_FNAME and "RU" in test_name:
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


# def run_test(handler):
#     print("Success")


if __name__ == "__main__":
    run_test(handler)
