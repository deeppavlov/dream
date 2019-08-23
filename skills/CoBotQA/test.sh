#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["Why is sky so blue?"]}' \
  http://0.0.0.0:3000/respond


curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["Who is Taylor Swift?", "Good morning"]}' \
  http://0.0.0.0:3000/respond
