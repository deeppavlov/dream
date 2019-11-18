#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["I like it"]}' \
  http://0.0.0.0:8025/attitude_annotations
