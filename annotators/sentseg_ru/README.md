# Sentence Segmentation model for Russian Language

Model adds punctuation marks (`.` and `?`) in Russian lower-cased text.

Models is trained on Russian Open Subtitles dataset using ruBERT-based NER setup. The training scores are the following:
```
{
    "valid": {
        "eval_examples_count": 28977, 
        "metrics": {
            "ner_f1": 73.9806, 
            "ner_token_f1": 73.9806
        }, 
        "time_spent": "0:00:36"
    }
}
{
    "test": {
        "eval_examples_count": 28976, 
        "metrics": {
            "ner_f1": 74.1223, 
            "ner_token_f1": 74.1223
        }, 
        "time_spent": "0:00:35"
    }
}
```
