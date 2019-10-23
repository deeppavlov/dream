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
 ["Great"],
 ["That nice"],
 ["Great"],
 ["Thanks"],
 ["Nice"],
 ["Wow!"],
 ["Where do you live?"]
 ]
}' \
 http://0.0.0.0:8014/detect

 curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": [
  ["Lets have a chat"],
  ["Lets chat about smth"],
  ["Lets chat about music"],
  ["Lets chat about music or cinema"],
  ["Lets chat about literature"],
  ["Lets chat about you"],
  ["Lets talk about you"],
  ["Lets talk about litarature"],
  ["Lets talk about Trump"],
  ["Lets talk about politics"],
  ["Lets talk about indie music"],
  ["Let'\''s chat about Taylor Swift"],
  ["Let'\''s chat about our president"],
  ["Let'\''s chat about recent movies"],
  ["Let'\''s talk about music"]
  ]
 }' \
  http://0.0.0.0:8014/detect
