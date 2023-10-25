#!/usr/bin/env bash

pip install locust

locust -f load_test.py -P 9000
