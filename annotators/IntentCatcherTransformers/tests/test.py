#!/usr/bin/env python

import requests
import json


def test_intent_catcher(url: str, tests: dict):
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
