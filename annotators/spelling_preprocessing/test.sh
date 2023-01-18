#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": ["thats great im here i just wanna be ur bets friend"]}' \
  http://0.0.0.0:8074/respond
