#!/usr/bin/env python

import requests
import json


def main_test():
    url = 'http://0.0.0.0:8057/respond'
    tests = json.load(open('tests.json'))
    for test in tests:
        req = requests.post(url=url, json=test['request'])
        assert req.ok, print(f"TEST FAILED! Status not OK.\nTest: {test}\nResult:{req.status_code}")
        if len(test['result']) > 0:
            phrase = req.json()[0][0]
            state = req.json()[0][3].get("short_story_skill_attributes", {})
            assert phrase in test['result']['phrases'], print(
                f"TEST FAILED! Wrong phrase.\nTest: {test}\nResult:{phrase}")
            assert state in test['result']['states'], print(
                f"TEST FAILED! Wrong state.\nTest: {test}\nResult:{state}")
    print("Success!")


if __name__ == '__main__':
    main_test()
