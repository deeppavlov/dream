#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"text": "hey alexa how are you"}' \
  http://0.0.0.0:3000/sentseg