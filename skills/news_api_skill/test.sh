#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["news about sport"]}' \
  http://0.0.0.0:3000/respond


curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["yes", "news about politics"]}' \
  http://0.0.0.0:3000/respond
