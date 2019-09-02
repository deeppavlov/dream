#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"conversations": [{"currentUtterance": "Hey!", "currentUtteranceTopic": "Phatic", "pastUtterances": [], "pastResponses": []}]}' \
  http://0.0.0.0:3000/dialogact


curl -H "Content-Type: application/json" -XPOST \
  -d '{"conversations": {"currentUtterance": "Good. Thank you. What do you know about Putin?", "currentUtteranceTopic": "Politics", "pastUtterances": ["Hey", "Hello. How are you doing?"], "pastResponses": []}}' \
  http://0.0.0.0:3000/dialogact
