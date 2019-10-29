 curl -H "Content-Type: application/json" -XPOST \
 -d '{"last_utterances":[["john peterson is my brother.", "he lives in New York."], ["my laptop was broken.", "could you show me the nearest store in Moscow where i can fix it."]]}' \
  http://0.0.0.0:8021/ner