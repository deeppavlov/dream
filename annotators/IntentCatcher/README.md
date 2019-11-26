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

| metrcis/intents | doing\_well         | exit                | opinion\_request    | repeat              | what\_can\_you\_do  | what\_is\_your\_job | what\_is\_your\_name | what\_time           | where\_are\_you\_from | who\_made\_you      |
|-----------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|----------------------|----------------------|-----------------------|---------------------|
| precision       | 1.0                | 0.9986974457504519 | 0.999929997166008  | 1.0                | 0.9692277553787851 | 0.9893557422969188 | 0.9778070175438597  | 0.6                 | 1.0                  | 0.9894012842017071 |
| recall          | 0.6756357527061861 | 0.8573418192612537 | 0.9956553011124954 | 0.9599164343607125 | 0.8769365951944664 | 0.7958150183150183 | 0.8675757575757576  | 0.17583333333333334 | 0.5075106890998946   | 0.944279238473919  |
| f1              | 0.8006250473470586 | 0.92247319304967   | 0.9977877933108547 | 0.9794638972745536 | 0.9166907012544364 | 0.879088559845207  | 0.9134540070143785  | 0.26178571428571434 | 0.6495771756728376   | 0.9656410935869314 |


## Getting started

В папке src/data должен быть tokenizer_english.pickle - токенайзер из NLTK.

Чтобы добавить интент, нужно:
 1. Вписать в `<intent_data_path>/intent_phrases.json` имя вашего интента, фразы/регекспы фраз, по которым будет идти матчинг, допустимые в этом случае знаки пунктуации, а также min_precision - минимально приемлимый precision для подбора трешхолда.
 2. Затем выполнить `python3 create_data.py <intent_data_path>/intent_phrases.json -p`, чтобы добавить эмбеддинги фраз, сами фразы (`-p` key) трешхолды и параметры для вычисления *confidence* (`-t` key). Они будут лежать в `<intent_data_path>/intent_data.json`
 3. Чтобы обучить **ClassifierDetector** на новых фразах (новых интентах). выполнить `python3 train_model.py --data_path <intent_data_path>/intent_data.json`.

Пример запуска внутри докера:
 ```
  python3 create_data.py /data/classifier_data/intent_phrases.json -p
  python /data/classifier_data/train_model.py --data_path /data/classifier_data/intent_data.json --model_path /data/classifier_data/models/linear_classifier.h5
``
