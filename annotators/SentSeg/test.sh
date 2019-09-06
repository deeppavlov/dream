#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["hey alexa how are you"]}' \
  http://0.0.0.0:8011/sentseg
