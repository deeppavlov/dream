#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["any fucks in this sentence"]}' \
  http://0.0.0.0:8018/blacklisted_words


curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["good one", "fucked one"]}' \
  http://0.0.0.0:8018/blacklisted_words
