#!/usr/bin/env python

import requests
import json
from os import getenv

INTENT_PHRASES_PATH = getenv("INTENT_PHRASES_PATH")


def main_test():
    url = "http://0.0.0.0:8200/rank"
    r = requests.post(
        url=url, json={"sentences": [["Give me overview of net sales by region"]]}
    )
    print(r)
    assert r.ok
    data = r.json()
    print(data)
    print("Success")


if __name__ == "__main__":
    main_test()
