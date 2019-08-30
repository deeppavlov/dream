#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["What do you know about something?"]}' \
  http://0.0.0.0:3000/topics


curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["This is my favorite one!", "This is my favorite movie!"]}' \
  http://0.0.0.0:3000/topics
