#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["I love watching movies."]}' \
  http://0.0.0.0:3000/sentiment


curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["I do not love watching movies", "I do not like movies but I love music"]}' \
  http://0.0.0.0:3000/sentiment
