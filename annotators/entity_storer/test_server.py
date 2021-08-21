import requests
import os

import common.test_utils as test_utils


SERVICE_PORT = os.getenv("SERVICE_PORT")
URL = f"http://0.0.0.0:{SERVICE_PORT}/respond"


def handler(requested_data):
    hypothesis = requests.post(URL, json=requested_data).json()
    return hypothesis


def run_test(handler):
    in_data, out_data = test_utils.get_dataset()
    for test_name in in_data:
        hypothesis = handler(in_data[test_name])
        print(f"test name: {test_name}")
        is_equal_flag, msg = test_utils.compare_structs(out_data[test_name], hypothesis)
        assert is_equal_flag, msg
        print("Success")


if __name__ == "__main__":
    run_test(handler)
