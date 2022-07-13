#!/usr/bin/env python

import requests
import json
from os import getenv

INTENT_PHRASES_PATH = getenv("INTENT_PHRASES_PATH")


def main_test():
    url = "http://0.0.0.0:8014/detect"
    # if "RU" in INTENT_PHRASES_PATH:
    #     tests = json.load(open("tests_RU.json"))
    # else:
    #     tests = json.load(open("tests.json"))

    tests = json.load(open("tests.json"))
    for test in tests:
        r = requests.post(url=url, json={"sentences": [[test["sentence"]]]})
        assert r.ok
        data = r.json()[0]
        if test["intent"] is not None:
            assert (
                data.get(test["intent"], {"detected": 0}).get("detected", 0) == 1
                and sum([v.get("detected", 0) for v in data.values()]) == 1
            ), print(f"TEST FAILED!\nTest: {test}\nResult:{json.dumps(data, indent=2)}")
        else:
            assert all([intent["detected"] == 0 for intent in data.values()]), f"test: {test}\nprediction: {data}"
    print("Success")


if __name__ == "__main__":
    main_test()
