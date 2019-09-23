#!/usr/bin/env bash

set -e
trap 'catch $? $LINENO' EXIT

catch() {
  echo "catching!"
  if [ "$1" != "0" ]; then
    # error handling goes here
    echo "Error $1 occurred on $2"

    echo "Down containers"
    docker-compose -f docker-compose.yml -f dev.yml -p dream_test down
  fi
}

echo "Up dp-agent"
docker-compose -f docker-compose.yml -f dev.yml -p dream_test up --build -d

echo "Pass dialogs from dp-agent"
docker-compose -f docker-compose.yml -f dev.yml -p dream_test exec agent python3 \
  utils/http_api_test.py -u http://0.0.0.0:4242 -df tests/dream/test_dialogs.json -of tests/dream/test_dialogs_output.csv

echo "Assert passed dialogs"
docker-compose -f docker-compose.yml -f dev.yml -p dream_test exec agent python3 tests/dream/assert_test_dialogs.py --file tests/dream/test_dialogs_output.csv

echo "Down containers"
docker-compose -f docker-compose.yml -f dev.yml -p dream_test down
