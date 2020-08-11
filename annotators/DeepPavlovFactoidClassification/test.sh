#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["who is Putin?"]}' \
  http://0.0.0.0:8073/factoid_annotations
