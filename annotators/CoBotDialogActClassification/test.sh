#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"conversations": [{"currentUtterance": "Hey!", "pastUtterances": [], "pastResponses": []}]}' \
  http://0.0.0.0:8006/dialogact


curl -H "Content-Type: application/json" -XPOST \
  -d '{"conversations": {"currentUtterance": "Good. Thank you. What do you know about Putin?", "pastUtterances": ["Hey", "Hello. How are you doing?"], "pastResponses": []}}' \
  http://0.0.0.0:8006/dialogact
