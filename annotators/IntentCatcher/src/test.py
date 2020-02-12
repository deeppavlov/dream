#!/usr/bin/env python

import requests
import json


def main_test():
    url = 'http://0.0.0.0:8014/detect'
    tests = json.load(open('tests.json'))
    for test in tests:
        r = requests.post(url=url, json={'sentences': [[test['sentence']]]})
        assert r.ok
        if test['intent'] is not None:
            assert r.json()[0].get(test['intent'], {'detected': 1}).get(
                'detected', 0) == 1, print(f"TEST FAILED!\nTest: {test}\nResult:{r.json()}")
        else:
            assert all([intent['detected'] == 0 for intent in r.json().values()])
    print("Success")


if __name__ == "__main__":
    main_test()
