# ODQA annotations

ODQA annotator outputs answer to the question and its confidence.
You can get ODQA annotations in your Flask application the following way:

```python
dialogs_batch = request.json["dialogs"]
for dialog in dialogs_batch:
    annotations = dialog["human_utterances"][-1]
    odqa_response = annotations["odqa"]
    answer = odqa_response["answer"]
    answer_sentence = odqa_response["answer_sentence"]
    confidence = odqa_response["confidence"]
    paragraph = odqa_response["paragraph"]
```

An example of odqa_response to the question "Who played Sheldon Cooper in the Big Bang Theory?":

{"answer": "James Joseph Parsons",

 "confidence": 0.99997,
 
 "answer_sentence": "James Joseph Parsons (born March 24, 1973) is an American actor.",
 
 "paragraph": 'James Joseph Parsons (born March 24, 1973) is an American actor.
               He is known for playing Sheldon Cooper in the CBS sitcom "The Big Bang Theory".
               He has received several awards for his performance, including four Primetime Emmy Awards
               for Outstanding Lead Actor in a Comedy Series and the Golden Globe Award for Best Actor in a
               Television Series Musical or Comedy.'}