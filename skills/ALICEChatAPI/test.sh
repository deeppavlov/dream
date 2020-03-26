#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences_batch": ["Are you bot or human?"]}' \
  http://0.0.0.0:8000/respond


curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences_batch": [["Hi!", "How are you?", "Do you know the text?"]]}' \
  http://0.0.0.0:8000/respond
