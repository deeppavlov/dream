curl -H "Content-Type: application/json" -XPOST \
 -d '{"candidates": ["I am cooking", "Am I walking?", "I was there yesterday", "I am in London", "I love Moscow"], "history": []}' \
  http://0.0.0.0:8131/conv_annot_candidate