## IntentCatcher based on Transformers


English version was trained on `intent_phrases.json` dataset using `DeepPavlov` library via command:
```
python -m deeppavlov train intents_model_dp_config.json
```

It consumes 3.5Gb GPU RAM during fine-tuning. Classification results after 5 epochs are the following:
```json
{"train": {"eval_examples_count": 183135, "metrics": {"accuracy": 0.9997, "f1_weighted": 1.0, "f1_macro": 0.9999, "roc_auc": 1.0}, "time_spent": "0:03:32"}}
{"valid": {"eval_examples_count": 78487, "metrics": {"accuracy": 0.9993, "f1_weighted": 0.9999, "f1_macro": 0.9998, "roc_auc": 1.0}, "time_spent": "0:01:33"}}

```


