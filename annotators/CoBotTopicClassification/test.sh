#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": [["What do you know about something?", "let'\''s chat about sports", "let'\''s chat"]]}' \
  http://0.0.0.0:8003/topics


curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": [["This is my favorite one!", "This is my favorite movie!"]]}' \
  http://0.0.0.0:8003/topics
