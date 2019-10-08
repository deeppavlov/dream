#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": [
    [
    "okay thats enough for today.",
    "bye bot."
    ],
    [
    "can you imagine!",
    "she ran away without saying goodbye!"
    ],
    [
    "He was ill.",
    "I took care of him."
    ]
  ]
}' \
  http://0.0.0.0:8014/detect


curl -H "Content-Type: application/json" -XPOST \
 -d '{"sentences": [
 ["alexa, i did not hear you, repeat"],
 ["alexa, i am a little deaf", "can you repeat please?"],
 ["be kind and repeat"],
 ["you are repeating it over and over!"],
 ["ok alexa have a good day!"]
 ]
}' \
 http://0.0.0.0:8014/detect
