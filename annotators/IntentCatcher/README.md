## Description

Детектор интентов. Каждый utterance приходит разбитый на предложения с помощью sentseg, каждое предложение
эмбеддится с помощью Universal sentence encoder (USE, https://arxiv.org/pdf/1803.11175.pdf).
В файле `src/detector.py` лежат различные детекторы.

## Описание детекторов:

- **USESimpleDetector**:  каждое предложение utterance сравнивается по метрике (*cosine similarity*) с предложениями интентов, берется максимум скора по всем предложениям и отсекается по трешхолду, вычисленному заранее.
- **USERegCombinedDetector**: каждое предложение сначала прогоняется через regexp, если же ни один интент не замэтчился - отправляем предложение в **USESimpleDetector**.
- **ClassifierDetector**: (линейный) классификатор, обученный поверх эмбеддингов USE.
- **ClassRegCombinedDetector** (TBD): то же самое что и **USERegCombinedDetector**, только c **ClassifierDetector**.

## TODO:

- Code refactoring
- train_model.py

## Метрики

**USERegCombinedDetector**:

| metrics/intents | exit        | repeat      | what\_is\_your\_name | where\_are\_you\_from | what\_can\_you\_do | who\_made\_you | what\_is\_your\_job |
|-----------------|-------------|-------------|----------------------|-----------------------|--------------------|----------------|---------------------|
| precision       | 0.933369776 | 0.819418869 | 0.996363636          | 0.958124098           | 0.851321586        | 0.876727199    | 0.92990404          |
| recall          | 0.617079005 | 0.731826007 | 0.818103175          | 0.87984127            | 0.72               | 0.877472177    | 0.905040404         |
| f1              | 0.735439153 | 0.767964591 | 0.893786162          | 0.909311858           | 0.670418219        | 0.874162102    | 0.912530126         |

**Linear classifier**

| metrics/intent | exit        | opinion\_request | repeat      | what\_can\_you\_do | what\_is\_your\_job | what\_is\_your\_name | where\_are\_you\_from | who\_made\_you |
|----------------|-------------|------------------|-------------|--------------------|---------------------|----------------------|-----------------------|----------------|
| precision      | 1           | 0.999985194      | 1           | 0.96547985         | 0.989626409         | 0.985909091          | 1                     | 0.988414623    |
| recall         | 0.863017994 | 0.997748446      | 0.835668442 | 0.89157764         | 0.779094619         | 0.852784091          | 0.535715411           | 0.970465581    |
| f1             | 0.926101846 | 0.998865489      | 0.909317355 | 0.922547939        | 0.867567083         | 0.907237682          | 0.684462705           | 0.978956695    |

## Getting started

В папке src/data должен быть tokenizer_english.pickle - токенайзер из NLTK.

Чтобы добавить интент, нужно:
 1. Вписать в `<intent_data_path>/intent_phrases.json` имя вашего интента, фразы/регекспы фраз, по которым будет идти матчинг, допустимые в этом случае знаки пунктуации, а также min_precision - минимально приемлимый precision для подбора трешхолда.
 2. Затем выполнить `python3 create_data.py <intent_data_path>/intent_phrases.json -p`, чтобы добавить эмбеддинги фраз, сами фразы (`-p` key) трешхолды и параметры для вычисления *confidence* (`-t` key). Они будут лежать в `<intent_data_path>/intent_data.json`
 3. Чтобы обучить **ClassifierDetector** на новых фразах (новых интентах). выполнить `python3 train_model.py` (WIP).

Пример запуска внутри докера:
 ```
  python3 create_data.py /data/classifier_data/intent_phrases.json -p
  python /data/classifier_data/train_model.py --data_path /data/classifier_data/intent_data.json --model_path /data/classifier_data/models/linear_classifier.h5
```
