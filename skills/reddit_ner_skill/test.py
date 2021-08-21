#!/usr/bin/env python

import requests
import json


def main_test():
    url = 'http://0.0.0.0:8035/respond'
    tests = json.load(open('tests.json'))
    for test in tests:
        assert requests.post(url=url, json=test).ok
    print("Success!")


if __name__ == '__main__':
    main_test()
