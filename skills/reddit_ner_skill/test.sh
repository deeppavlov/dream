#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
    -d '{"ner": [[[], [{"text":"united states", "confidence":0.9, "type": "GEO"}]]], "sentiment": [{"text":["neutral",  0.6]}], "intent": [{"yes": {"detected": 0.0}, "no":{"detected":0.0}}], "continuation":[0]}' \
    http://0.0.0.0:8035/respond


curl -H "Content-Type: application/json" -XPOST \
    -d '{"ner": [[]], "sentiment": [{"text":["positive", 0.8]}], "intent": [{"yes": {"detected": 1.0}, "no": {"detected": 0.0}}], "continuation": [1]}' \
    http://0.0.0.0:8035/respond
