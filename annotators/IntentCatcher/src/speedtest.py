#!/usr/bin/env python

import requests
import json
import time
import numpy as np


def main_test():
    loops = 20
    url = "http://0.0.0.0:8014/detect"
    tests = json.load(open("tests.json"))
    times = []
    for i in range(loops):
        for test in tests:
            start = time.time()
            requests.post(url=url, json={"sentences": [[test["sentence"]]]})
            times.append(time.time() - start)
    print(f"Mean time for {loops} loops: {np.mean(times)}")


if __name__ == "__main__":
    main_test()
