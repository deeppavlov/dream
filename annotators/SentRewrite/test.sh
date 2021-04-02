 curl -H "Content-Type: application/json" -XPOST \
 -d '{"utterances_histories":[["do you know lionel messi?", "yes, he is a football player.", "who is the best, he or c.ronaldo?"], ["hi alexa. do you know lionel messi?", "he is the best football player.", "really, i dont know him."], ["hi alexa", "hi my friend. long time no see."]]}' \
  http://0.0.0.0:8017/sentrewrite

curl -H "Content-Type: application/json" -XPOST \
 -d '{"utterances_histories":[["john peterson is my uncle. he is a teacher. do you know him", "no. i dont know him."]]}' \
  http://0.0.0.0:8017/sentrewrite