 curl -H "Content-Type: application/json" -XPOST \
 -d '{"sentences":["john peterson is my brother.", "he is studying in mipt university which is located in moscow."]}' \
  http://0.0.0.0:8021/ner

curl -H "Content-Type: application/json" -XPOST \
 -d '{"sentences":["michael johnson is my uncle.", "he is a teacher.", "do you know him", "i dont know him."]}' \
  http://0.0.0.0:8021/ner
