# Sentence Segmentation model for Russian Language

Model adds punctuation marks (`.` and `?`) in Russian lower-cased text.

Models is trained on Russian Open Subtitles dataset using NER setup. The training scores are the following:
```
{
    "valid": {
        "eval_examples_count": 2153, 
        "metrics": {
            "ner_f1": 95.6427, 
            "ner_token_f1": 97.3442
        }, 
        "time_spent": "0:00:08"
    }
}
{
    "test": {
        "eval_examples_count": 1922, 
        "metrics": {
            "ner_f1": 94.8523, 
            "ner_token_f1": 96.9718
        }, 
        "time_spent": "0:00:08"
    }
}
```
