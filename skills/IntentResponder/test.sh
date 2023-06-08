#!/bin/bash

curl -H "Content-Type: application/json" -XPOST \
  -d '{
    "user_utterances": [
      "I am so happy to hear that, bye",
      "That is very upsetting, but i have to go. Have a good day"
    ],
    "bot_utterances": [
      "My battery is full. You can remove the charger",
      "It is going to rain in a few hours"
    ],
    "annotations": [
  {
    "intent_catcher": {
      "exit" : {
        "detected" : 1,
        "confidence" : 0.87
      },
      "repeat" : {
        "detected" : 0,
        "confidence" : 0.2
      }
    },
    "cobot_offensiveness": {
      "text": "non-toxic",
      "confidence":0.95,
      "is_badlisted":"not badlist"
    }
  },
  {
    "intent_catcher": {
      "exit" : {
        "detected" : 1,
        "confidence" : 0.95
      },
      "repeat" : {
        "detected" : 0,
        "confidence" : 0.1
      }
    },
     "cobot_offensiveness": {
      "text": "non-toxic",
      "confidence":0.95,
      "is_badlisted":"not badlist"
    }
  }
  ]
}' \
  http://0.0.0.0:8012/respond


curl -H "Content-Type: application/json" -XPOST \
 -d '{
   "user_utterances": [
     "Oh i did not hear you stupid Alexa",
     "Could you just repeat?"
   ],
   "bot_utterances": [
     "",
     "Bla bla bla #+#repeat #+#exit"
   ],
   "annotations": [
 {
   "intent_catcher": {
    "exit" : {
      "detected" : 0,
      "confidence" : 0.53
   },
    "repeat" : {
      "detected" : 1,
      "confidence" : 0.79
   }
 },
 "cobot_offensiveness":{
     "text": "toxic",
     "confidence":0.95,
     "is_badlisted":"not badlist"
   }
 },
 {
   "intent_catcher": {
    "exit" : {
      "detected" : 1,
      "confidence" : 0.89
   },
   "repeat" : {
     "detected" : 1,
     "confidence" : 0.90
   }
 },
 "cobot_offensiveness":{
     "text": "toxic",
     "confidence":0.95,
     "is_badlisted":"badlist"
   }
 }
 ]
}' \
 http://0.0.0.0:8012/respond
