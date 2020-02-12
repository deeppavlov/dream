#!/usr/bin/env python

import requests
import json

def main_test():
    url = 'http://0.0.0.0:8014/detect'
    tests = json.load(open('tests.json'))

if __name__ == "__main__":
    main_test()
