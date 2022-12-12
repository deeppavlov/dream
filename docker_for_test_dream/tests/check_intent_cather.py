#!/usr/bin/env python

import requests


tests = [
    {"sentence": "track people please", "intent": "track_object"},
    {"sentence": "left turn 20", "intent": "turn_around"},
    {"sentence": "Please move forward 20 metres", "intent": "move_forward"},
    {"sentence": "Robot move backward 13", "intent": "move_backward"},
]


def main_test():
    url = "http://0.0.0.0:8014/detect"

    for test in tests:
        r = requests.post(url=url, json={"sentences": [[test["sentence"]]]})

        data = r.json()[0]
        print("=============")
        print(data)


if __name__ == "__main__":
    main_test()
