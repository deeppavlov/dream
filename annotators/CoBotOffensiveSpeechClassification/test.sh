#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["you are not smart"]}' \
  http://0.0.0.0:8005/offensiveness


curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["fuck! this is awesome", "you are moron!"]}' \
  http://0.0.0.0:8005/offensiveness
