import os

import requests

import common.test_utils as test_utils


PORT = int(os.getenv("PORT"))
RANDOM_SEED = int(os.getenv("RANDOM_SEED", 2718))
URL = f"http://0.0.0.0:{PORT}/model"


def handler(requested_data, random_seed):
    hypothesis = requests.post(URL, json={**requested_data, "random_seed": random_seed}).json()
    return hypothesis


def run_test(handler) -> None:
    in_data, out_data = test_utils.get_dataset()
    for test_name in in_data:
        print(f"test name: {test_name}")
        cur_in_test = in_data[test_name]
        cur_out_test = out_data[test_name]
        for cur_in_data, cur_out_data in zip(cur_in_test, cur_out_test):
            cur_real_out_data = handler(cur_in_data, RANDOM_SEED)
            cur_real_out_data = cur_real_out_data[0]["facts"]

            assert all(
                [fact in cur_out_data for fact in cur_real_out_data]
            ), f"expect out: {cur_out_data}\n real out: {cur_real_out_data}"

    print("Success")


if __name__ == "__main__":
    run_test(handler)
