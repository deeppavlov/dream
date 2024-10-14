import allure
import requests
import time
import pytest
import os

from common import test_utils


SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8025))
RANDOM_SEED = int(os.getenv("RANDOM_SEED", 2718))
URL = f"http://0.0.0.0:{SERVICE_PORT}/respond"


def handler(requested_data, random_seed):
    hypothesis = requests.post(URL, json={**requested_data, "random_seed": random_seed}).json()
    return hypothesis


@allure.description("""4.1.2 Test input and output data types""")
def test_in_out():
    in_data, _ = test_utils.get_dataset()
    print(_)
    for _, test in in_data.items():
        hypothesis = handler(test, RANDOM_SEED)
    assert isinstance(test, (dict, list)), "Invalid input type"
    assert isinstance(hypothesis, (dict, list)), "Invalid output type"


@allure.description("""4.1.3 Test execution time""")
def test_exec_time():
    start = time.time()
    in_data, _ = test_utils.get_dataset()
    print(_)
    for _, test in in_data.items():
        handler(test, RANDOM_SEED)
    assert time.time() - start <= 0.4, "Unsufficient run time"


@pytest.mark.parametrize("handler", [handler])
@allure.description("""Execution test""")
def test_run(handler):
    in_data, out_data = test_utils.get_dataset()
    for test_name in in_data:
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
    test_run(handler)
