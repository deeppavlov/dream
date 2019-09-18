#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["shit happens"]}' \
  http://0.0.0.0:8013/toxicity_annotations
