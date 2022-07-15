 curl -H "Content-Type: application/json" -XPOST \
 -d '{"last_utterances":[["turn 10 degrees clockwise in Moscow.", "move forward ten metres."],
     ["you must track red car and people.", "drive backward nine meters."]]}' \
  http://0.0.0.0:8021/ner