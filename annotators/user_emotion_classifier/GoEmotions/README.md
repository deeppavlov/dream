# GoEmotions Pytorch

Pytorch Implementation of [GoEmotions](https://github.com/google-research/google-research/tree/master/goemotions) with [Huggingface Transformers](https://github.com/huggingface/transformers)

## What is GoEmotions

Dataset labeled **58000 Reddit comments** with **28 emotions**

- admiration, amusement, anger, annoyance, approval, caring, confusion, curiosity, desire, disappointment, disapproval, disgust, embarrassment, excitement, fear, gratitude, grief, joy, love, nervousness, optimism, pride, realization, relief, remorse, sadness, surprise + neutral

## Training Details

- Use `bert-base-cased` (Same as the paper's code)
- In paper, **3 Taxonomies** were used. I've also made the data with new taxonomy labels for `hierarchical grouping` and `ekman`.

  1. **Original GoEmotions** (27 emotions + neutral)
  2. **Hierarchical Grouping** (positive, negative, ambiguous + neutral)
  3. **Ekman** (anger, disgust, fear, joy, sadness, surprise + neutral)

### Vocabulary

- I've replace `[unused1]`, `[unused2]` to `[NAME]`, `[RELIGION]` in the vocab, respectively.

```text
[PAD]
[NAME]
[RELIGION]
[unused3]
[unused4]
...
```

- I've also set `special_tokens_map.json` as below, so the tokenizer won't split the `[NAME]` or `[RELIGION]` into its word pieces.

```json
{
  "unk_token": "[UNK]",
  "sep_token": "[SEP]",
  "pad_token": "[PAD]",
  "cls_token": "[CLS]",
  "mask_token": "[MASK]",
  "additional_special_tokens": ["[NAME]", "[RELIGION]"]
}
```

### Requirements

- torch==1.4.0
- transformers==2.11.0
- attrdict==2.0.1

### Hyperparameters

You can change the parameters from the json files in `config` directory.

| Parameter         |      |
| ----------------- | ---: |
| Learning rate     | 5e-5 |
| Warmup proportion |  0.1 |
| Epochs            |   10 |
| Max Seq Length    |   50 |
| Batch size        |   16 |

## How to Run

For taxonomy, choose `original`, `group` or `ekman`

```bash
$ python3 run_goemotions.py --taxonomy {$TAXONOMY}

$ python3 run_goemotions.py --taxonomy original
$ python3 run_goemotions.py --taxonomy group
$ python3 run_goemotions.py --taxonomy ekman
```

## Results

Best Result of `Macro F1`

| Macro F1 (%) |  Dev  | Test  |
| ------------ | :---: | :---: |
| original     | 50.16 | 50.30 |
| group        | 69.41 | 70.06 |
| ekman        | 62.59 | 62.38 |

## Pipeline

- Inference for multi-label classification was made possible by creating a new `MultiLabelPipeline` class.
- Already uploaded `finetuned model` on Huggingface S3.
  - Original GoEmotions Taxonomy: `monologg/bert-base-cased-goemotions-original`
  - Hierarchical Group Taxonomy: `monologg/bert-base-cased-goemotions-group`
  - Ekman Taxonomy: `monologg/bert-base-cased-goemotions-ekman`

### 1. Original GoEmotions Taxonomy

```python
from transformers import BertTokenizer
from model import BertForMultiLabelClassification
from multilabel_pipeline import MultiLabelPipeline
from pprint import pprint

tokenizer = BertTokenizer.from_pretrained("monologg/bert-base-cased-goemotions-original")
model = BertForMultiLabelClassification.from_pretrained("monologg/bert-base-cased-goemotions-original")

goemotions = MultiLabelPipeline(
    model=model,
    tokenizer=tokenizer,
    threshold=0.3
)

texts = [
    "Hey that's a thought! Maybe we need [NAME] to be the celebrity vaccine endorsement!",
    "it’s happened before?! love my hometown of beautiful new ken 😂😂",
    "I love you, brother.",
    "Troll, bro. They know they're saying stupid shit. The motherfucker does nothing but stink up libertarian subs talking shit",
]

pprint(goemotions(texts))

# Output
 [{'labels': ['neutral'], 'scores': [0.9750906]},
 {'labels': ['curiosity', 'love'], 'scores': [0.9694574, 0.9227462]},
 {'labels': ['love'], 'scores': [0.993483]},
 {'labels': ['anger'], 'scores': [0.99225825]}]
```


### 2. Group Taxonomy

```python
from transformers import BertTokenizer
from model import BertForMultiLabelClassification
from multilabel_pipeline import MultiLabelPipeline
from pprint import pprint

tokenizer = BertTokenizer.from_pretrained("monologg/bert-base-cased-goemotions-group")
model = BertForMultiLabelClassification.from_pretrained("monologg/bert-base-cased-goemotions-group")

goemotions = MultiLabelPipeline(
    model=model,
    tokenizer=tokenizer,
    threshold=0.3
)

texts = [
    "Hey that's a thought! Maybe we need [NAME] to be the celebrity vaccine endorsement!",
    "it’s happened before?! love my hometown of beautiful new ken 😂😂",
    "I love you, brother.",
    "Troll, bro. They know they're saying stupid shit. The motherfucker does nothing but stink up libertarian subs talking shit",
]

pprint(goemotions(texts))

# Output
[{'labels': ['positive'], 'scores': [0.9989434]},
 {'labels': ['ambiguous', 'positive'], 'scores': [0.99801123, 0.99845874]},
 {'labels': ['positive'], 'scores': [0.99930394]},
 {'labels': ['negative'], 'scores': [0.9984231]}]
```

### 3. Ekman Taxonomy

```python
from transformers import BertTokenizer
from model import BertForMultiLabelClassification
from multilabel_pipeline import MultiLabelPipeline
from pprint import pprint

tokenizer = BertTokenizer.from_pretrained("monologg/bert-base-cased-goemotions-ekman")
model = BertForMultiLabelClassification.from_pretrained("monologg/bert-base-cased-goemotions-ekman")

goemotions = MultiLabelPipeline(
    model=model,
    tokenizer=tokenizer,
    threshold=0.3
)

texts = [
    "Hey that's a thought! Maybe we need [NAME] to be the celebrity vaccine endorsement!",
    "it’s happened before?! love my hometown of beautiful new ken 😂😂",
    "I love you, brother.",
    "Troll, bro. They know they're saying stupid shit. The motherfucker does nothing but stink up libertarian subs talking shit",
]

pprint(goemotions(texts))

# Output
 [{'labels': ['joy', 'neutral'], 'scores': [0.30459446, 0.9217335]},
 {'labels': ['joy', 'surprise'], 'scores': [0.9981395, 0.99863845]},
 {'labels': ['joy'], 'scores': [0.99910116]},
 {'labels': ['anger'], 'scores': [0.9984291]}]
```

## Reference

- [GoEmotions](https://github.com/google-research/google-research/tree/master/goemotions)
- [GoEmotions Github](https://github.com/google-research/google-research/tree/master/goemotions)
- [Huggingface Transformers](https://github.com/huggingface/transformers)
