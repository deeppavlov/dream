import requests
import os
import pathlib
import json

import common.test_utils as test_utils


SERVICE_PORT = os.getenv("SERVICE_PORT")
URL = f"http://0.0.0.0:{SERVICE_PORT}/respond"


def get_tests(postfix):
    return {
        file.name.replace(postfix, ""): json.load(file.open("rt"))
        for file in pathlib.Path("tests/").glob(f"*{postfix}")
    }


in_data = get_tests("_in.json")
out_data = get_tests("_out.json")
assert set(in_data) == set(out_data), "All files must be in pairs."


def main():
    for test_name in in_data:
        hypothesis = requests.post(URL, json=in_data[test_name]).json()
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
    main()
