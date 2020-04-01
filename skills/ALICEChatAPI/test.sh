#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences_batch": [["I am GGGGG."]]}' \
  http://0.0.0.0:8000/respond

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences_batch": [["i am not", "i missed you that", "hang up walking", "yes"]]}' \
  http://0.0.0.0:8000/respond

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences_batch": [["Are you bot or human?"]]}' \
  http://0.0.0.0:8000/respond

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences_batch": [["Where are you located"]]}' \
  http://0.0.0.0:8000/respond


curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences_batch": [["Hi!", "How are you?", "Do you know the text?"]]}' \
  http://0.0.0.0:8000/respond
