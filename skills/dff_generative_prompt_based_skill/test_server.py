import requests
import os

import common.test_utils as test_utils


SERVICE_PORT = int(os.getenv("SERVICE_PORT"))
RANDOM_SEED = int(os.getenv("RANDOM_SEED", 2718))
URL = f"http://0.0.0.0:{SERVICE_PORT}/respond"


def handler(requested_data, random_seed):
    hypothesis = requests.post(URL, json={**requested_data, "random_seed": random_seed}, timeout=4).json()
    return hypothesis


def run_test(handler):
    in_data, out_data = test_utils.get_dataset()
    for test_name in in_data:
        hypothesis = handler(in_data[test_name], RANDOM_SEED)
        # do not compare first elements of the structs - generated texts
        is_equal_flag, msg = test_utils.compare_structs(
            out_data[test_name][1:], hypothesis[1:], ignored_keys=["id", "responses"]
        )
        if msg and len(msg.split("`")) == 3:
            _, ground_truth_text, _, hypothesis_text, _ = msg.split("`")
            is_equal_flag, ratio = test_utils.compare_text(ground_truth_text, hypothesis_text, 0.2)
            if not is_equal_flag:
                msg = f"{msg} ratio = {ratio}"
        assert is_equal_flag, msg
        print("Success")


if __name__ == "__main__":
    run_test(handler)
