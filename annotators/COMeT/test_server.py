import requests
import os

import common.test_utils as test_utils

SERVICE_NAME = os.getenv("SERVICE_NAME")
SERVICE_PORT = int(os.getenv("SERVICE_PORT"))
URL = f"http://0.0.0.0:{SERVICE_PORT}/comet"


def handler(requested_data):
    hypothesis = requests.post(URL, json={**requested_data}).json()
    return hypothesis


def run_test(handler):
    in_data, out_data = test_utils.get_dataset()
    for test_name in in_data:
        if test_name in SERVICE_NAME:
            hypothesis = handler(in_data[test_name])
            print(f"test name: {test_name}")
            is_equal_flag, msg = test_utils.compare_structs(out_data[test_name], hypothesis)
            if msg and len(msg.split("`")) == 5:
                _, ground_truth_text, _, hypothesis_text, _ = msg.split("`")
                is_equal_flag, ratio = test_utils.compare_text(ground_truth_text, hypothesis_text, 0.80)
                if not is_equal_flag:
                    msg = f"{msg} ratio = {ratio}"
            assert is_equal_flag, msg
            print("Success")


if __name__ == "__main__":
    run_test(handler)