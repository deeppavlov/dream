#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": [
    [
    "Okay thats enough for today.",
    "Bye bot."
    ],
    [
    "Can you imagine!",
    "She ran away without saying goodbye!"
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
 ["Alexa, i did not hear you, repeat"],
 ["Alexa, i am a little deaf", "Can you repeat please?"],
 ["Please, repeat"],
 ["You are repeating it over and over!"],
 ["Okay, Alexa, have a good day!"],
 ["Okay"],
 ["That nice"],
 ["Nice"],
 ["Wow!"]
 ]
}' \
 http://0.0.0.0:8014/detect
