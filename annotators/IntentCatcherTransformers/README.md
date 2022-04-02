## IntentCatcher based on Transformers


English version was trained on `intent_phrases.json` dataset via command:
```
python create_data_and_train_model.py --intent_phrases_path intent_phrases.json --model_path ./data/intents_model_v0 --epochs 5
```
It consumes 2 Gb GPU RAM during fine-tuning `distilbert-base-uncased`. Classification results are the following:
```json
{
 'eval_loss': 0.00012610587873496115, 
 'eval_f1': 0.9994798460344262, 
 'eval_roc_auc': 0.999754199422437,
 'eval_accuracy': 0.99942380639895,
 'eval_runtime': 106.2084,
 'eval_samples_per_second': 588.268,
 'epoch': 5.0
}
```


