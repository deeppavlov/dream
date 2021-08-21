# KBQA annotations

KBQA annotator outputs answer to the question and its confidence.
You can get KBQA annotations in your Flask application the following way:

```python
dialogs_batch = request.json["dialogs"]
for dialog in dialogs_batch:
    annotations = dialog["human_utterances"][-1]
    kbqa_response = annotations["kbqa"]
    answer = kbqa_response["answer"]
    confidence = kbqa_response["confidence"]
```

An example of kbqa_response to to question "What is the capital of Russia?":

{"answer": "Moscow is the capital of Russia.",

 "confidence": 0.0}
