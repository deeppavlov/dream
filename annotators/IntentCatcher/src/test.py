#!/usr/bin/env python

import requests
import json


def main_test():
    url = "http://0.0.0.0:8014/detect"
    tests = json.load(open("tests.json"))
    for test in tests:
        r = requests.post(url=url, json={"sentences": [[test["sentence"]]]})
        assert r.ok
        data = r.json()[0]
        if test["intent"] is not None:
            assert (
                data.get(test["intent"], {"detected": 0}).get("detected", 0) == 1
                and sum([v.get("detected", 0) for v in data.values()]) == 1
            ), print(f"TEST FAILED!\nTest: {test}\nResult:{data}")
        else:
            assert all([intent["detected"] == 0 for intent in data.values()]), f"test: {test}\nprediction: {data}"
    print("Success")


if __name__ == "__main__":
    main_test()
