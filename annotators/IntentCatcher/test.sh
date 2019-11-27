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
  ["i want to commit a suicide today."],
  ["Hello there!"],
  ["How are you?"],
  ["I want to bring peace out here"],
  ["Where do you live?"],
  ["See you later"],
  ["Talk to you later"],
  ["What are you able to do?"],
  ["How can I call you?"],
  ["I am from US, and you?"],
  ["Lets chat about music or cinema"],
  ["Do you know Donald Trump"],
  ["OK, take care, bye!"],
  ["See ya, Alexa"],
  ["I have seen a shop nearby"],
  ["Would you recommend me smth?"],
  ["Hi there"],
  ["Ok, see you next week!"]
  ]
 }' \
  http://0.0.0.0:8014/detect

curl -H "Content-Type: application/json" -XPOST \
  -d '{"sentences": [
  ["End conversation"],
  ["Let end this conversation"],
  ["Stop dialog"],
  ["Alexa, end"],
  ["How do i end this dialog?"],
  ["Play in the end"],
  ["Stop it, Alexa"]
  ]
 }' \
  http://0.0.0.0:8014/detect



curl -H "Content-Type: application/json" -XPOST \
   -d '{"sentences": [
   ["What to do if a man pass out?"],
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
   ["Wow"],
   ["Nice one"],
   ["Do not"],
   ["No"],
   ["Dont do this"],
   ["Absolutely not"],
   ["Absolutely yes"],
   ["Lets chat"]
   ["Yeah, sure"],
   ["Sure, go ahead"]
   ]
  }' \
   http://0.0.0.0:8014/detect
