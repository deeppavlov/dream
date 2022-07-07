#!/usr/bin/env python

import requests
import json


def main_test():
    url = "http://0.0.0.0:8014/detect"
    tests = json.load(open("tests.json"))
    for test in tests:
        r = requests.post(url=url, json={"sentences": [[test["sentence"]]]})
        if not r.ok:
            print(f"Request status not ok: {test}")
        data = r.json()[0]
        if test["intent"] is not None:
            condition = data.get(test["intent"], {"detected": 0}).get("detected", 0) == 1
            condition = condition and sum([v.get("detected", 0) for v in data.values()]) == 1
            if not condition:
                data = {intent: data[intent]["confidence"] for intent in data if data[intent]["detected"]}
                print(f"Test failed:{test}\nprediction: {data}")
        else:
            if not all([intent["detected"] == 0 for intent in data.values()]):
                data = {intent: data[intent]["confidence"] for intent in data if data[intent]["detected"]}
                print(f"Test failed: {test}\nprediction: {data}")
    print("Success")


if __name__ == "__main__":
    main_test()
