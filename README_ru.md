# DeepPavlov Dream

**DeepPavlov Dream**  -- это платформа для создания модульный диалоговых систем.

Документация архитектуры для DeepPavlov Agent может быть найдена на [readthedocs documentation](https://deeppavlov-agent.readthedocs.io).

# Дистрибутивы

На данный момент представлены 6 дистрибутивов: 
- полная версия англоязычного бота DREAM (основан на версии бота, участвовавшего в lexa Prize Challenge)
- 4 дистрибутива Deepy представляют собой легкие версии бота на английском языке,
- русскоязычная диалоговая система, в основе которой лежит генеративная модель DialoGPT Russian.


### Deepy Base
Базовая версия Lunar assistant.
Deepy Base содержит аннотатор исправления опечаток Spelling Preprocessing,
шаблонный навык Harvesters Maintenance Skill
и навык открытого домена на основе AIML, написанный на Dialog Flow Framework. 

### Deepy Advanced
Расширенная версия Lunar assistant.
Deepy Advanced содержит аннотаторы исправления опечаток Spelling Preprocessing, 
разделения текста на предложения Sentence Segmentation,
связывания сущностей Entity Linking и детектирвоания специальный намерений Intent Catcher, 
навык Harvesters Maintenance GoBot Skill для целеориентированных ответов,
и навык открытого домена на основе AIML, написанный на Dialog Flow Framework. 

### Deepy FAQ
FAQ-версия (Frequently-asked Questions) Lunar assistant.
Deepy FAQ содержит аннотатор исправления опечаток Spelling Preprocessing, 
навык Frequently Asked Questions Skill на основе шаблонов,
и навык открытого домена на основе AIML, написанный на Dialog Flow Framework. 

### Deepy GoBot
Целеориентированная версия Lunar assistant.
Deepy GoBot Base содержит аннотатор исправления опечаток Spelling Preprocessing, 
навык Harvesters Maintenance GoBot Skill для целеориентированных ответов,
и навык открытого домена на основе AIML, написанный на Dialog Flow Framework. 

### Dream
Полная версия DeepPavlov Dream Socialbot на английском языке.
Данная версия практически идентична DREAM socialbot из 
[the end of Alexa Prize Challenge 4](https://d7qzviu3xw2xc.cloudfront.net/alexa/alexaprize/docs/sgc4/MIPT-DREAM.pdf).
Некоторые API сервисы заменены на обучаемые модели.
Некоторые сервисы (например, News Annotator, Game Skill, Weather Skill) требуют использования приватных 
ключей для использования  API сервисов, большинство распространяются бесплатно.
Если вы хотите использовать эти сервисы в локальной версии бота, добавьте свои ключи в переменные окружения 
(например, `./.env`).
Данная версия Dream Socialbot потребляет много ресурсов в связи с модульной архитектурой и изначальными целями 
(участие в Alexa Prize Challenge). Демо-версия бота для общения представлена на [нашем сайте](https://demo.deeppavlov.ai).


### Dream Mini
Мини-версия DeepPavlov Dream Socialbot.
Данная версия основана на нейросетевой генерации с использованием [English DialoGPT модели](https://huggingface.co/microsoft/DialoGPT-medium). 
Дистрибутив также содержит компоненты для детектирования запросов пользователя и выдачи специальных ответов на них.
[Link to the distribution.](https://github.com/deeppavlov/dream/tree/main/assistant_dists/dream_mini)

### Dream Russian
Русскоязычная версия  DeepPavlov Dream Socialbot. Данная версия основана на нейросетевой генерации с использованием
[Russian DialoGPT модели by DeepPavlov](https://huggingface.co/DeepPavlov/rudialogpt3_medium_based_on_gpt2_v2). 
Дистрибутив также содержит компоненты для детектирования запросов пользователя и выдачи специальных ответов на них.
[Link to the distribution.](https://github.com/deeppavlov/dream/tree/main/assistant_dists/dream_russian)

# Quick Start

### Склонируйте репозиторий

```
git clone https://github.com/deeppavlov/dream.git
```


### Установите  [docker](https://docs.docker.com/engine/install/) и [docker-compose](https://docs.docker.com/compose/install/) 

Если вы получаете ошибку  "Permission denied" во время запуска docker-compose, 
убедитесь, что [ваш докер клиент сконфигурирован](https://docs.docker.com/engine/install/linux-postinstall/) правильно.


### Запустите один из дистрибутивов  Dream 

#### **Deepy**

Подставьте вместо `VERSION` нужное название дистрибутива: `deepy_base`, `deepy_adv`, `deepy_faq`, `deepy_gobot_base`.

```
docker-compose -f docker-compose.yml -f assistant_dists/VERSION/docker-compose.override.yml up --build
```

#### **Dream (с использованием proxy)**
Простейший способ испольховать  Dream - поднимать бота с помощью proxy-сервисов. 
Все запросы будут перенаправлены на DeepPavlov API, поэтому вам не потребуется большое число ресурсов. 
Локально поднимаются только агент и база данные mongo.
См. [использование proxy](#proxy-usage).
```
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml -f assistant_dists/dream/proxy.yml up --build
```

#### **Dream (локально)**

**Данный дистрибутив DeepPavlov Dream требует крайне много вычислительных ресурсов.**
Для оценки требований можно обратиться к разделу [Компоненты](#components).
```
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml up --build
```
Мы также предоставляем конфигурационный файл (`assistant_dists/dream/test.yml`) для распределения по GPU для серверов с несколькими доступными GPU.

```
AGENT_PORT=4242 docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml -f assistant_dists/dream/test.yml up
```
Если естьнеобходимость перезапустить определенный контейнер без re-building (убедитесь, что маппинг папок в `assistant_dists/dream/dev.yml` правильный):
```
AGENT_PORT=4242 docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml restart container-name
```

### Использование

DeepPavlov Agent предоставляет 3 варианта взаимодействия: через интерфейс командной строки, API и Телеграм-бот

#### CLI
В отдельной вкладке терминала запустите:

```
docker-compose exec agent python -m deeppavlov_agent.run agent.channel=cmd agent.pipeline_config=assistant_dists/dream/pipeline_conf.json
```

Введите имя пользователя и можете начать общаться с Dream!

#### HTTP API
Как только вы подняли бота, Agent API станет доступен по адресу `http://localhost:4242`.
Узнать больше про API можно в [DeepPavlov Agent Docs](https://deeppavlov-agent.readthedocs.io/en/latest/intro/overview.html#http-api-server).

Браузерный интерфейс чата в DeepPavlov Agent доступен по адресу `http://localhost:4242/chat'.

#### Telegram Bot
На данный момент Телеграм-бот разворачивается **вместо** HTTP API
Измените определение `agent` `command` внутри `docker-compose.override.yml`:
```
agent:
  command: sh -c 'bin/wait && python -m deeppavlov_agent.run agent.channel=telegram agent.telegram_token=<TELEGRAM_BOT_TOKEN> agent.pipeline_config=assistant_dists/dream/pipeline_conf.json'
```
**ВАЖНО:** Не храните токен бота в открытом репозитории!

# Конфигурация и использование proxy 
Dream использует несколько конфигурационных файлов для docker-compose:

`./docker-compose.yml` -- основной файл, включающий контейнеры агента DeepPavlov Agent и базы данных mongo;

`./assistant_dists/*/docker-compose.override.yml` содержит все компоненты для дистрибутива и их основные параметры; 

`./assistant_dists/dream/dev.yml` включает маппинг папок (volume binding) для более простой отладки;

`./assistant_dists/dream/test.yml` содержит перераспределение по доступным GPU;

`./assistant_dists/dream/proxy.yml` содержит список proxy-контейнеров.

Если ваши ресурсы ограничены, вы можете заменить некоторые (например, все, кроме тех, что вы разрабатываете локально) 
контейнеры на proxy-версии, поднятые DeepPavlov. 
Для этого, убедитесь, что они определены в  `proxy.yml`, например.:
```
convers-evaluator-annotator:
  command: ["nginx", "-g", "daemon off;"]
  build:
    context: dp/proxy/
    dockerfile: Dockerfile
  environment:
    - PROXY_PASS=dream.deeppavlov.ai:8004
    - PORT=8004
```
и включайте этот файл в команду запуска:

```
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml -f assistant_dists/dream/proxy.yml up --build
```

По умолчанию, `proxy.yml` содержит все контейнеры кроме агента и базы данных.


# Компоненты  Russian Dream

Архитектура Russian Dream  представлена на изображении:
![DREAM](RussianDREAM.png)

| Name                | Requirements | Description                                                                                                                                                                    |
|---------------------|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Rule Based Selector |              | Algorithm that selects list of skills to generate candidate responses to the current context based on topics, entities, emotions, toxicity, dialogue acts and dialogue history |
| Response Selector   | 50 MB RAM    | Algorithm that selects a final responses among the given list of candidate responses                                                                                           |

## Annotators

| Name                   | Requirements            | Description                                                                                                                                                                                  |
|------------------------|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Badlisted Words        | 50 MB RAM               | detects obscene Russian words from the badlist                                                                                                                                               |
| Entity Detection       | 5.5 GB RAM              | extracts entities and their types from utterances                                                                                                                                            |
| Entity Linking         | 400 MB RAM              | finds Wikidata entity ids for the entities detected with Entity Detection                                                                                                                    |
| Fact Retrieval         | 6.5 GiB RAM, 1 GiB GPU  | Аннотатор извлечения параграфов Википедии, релевантных истории диалога.                                                                                                                      |
| Intent Catcher         | 900 MB RAM              | classifies user utterances into a number of predefined intents which are trained on a set of phrases and regexps                                                                             |
| NER                    | 1.7 GB RAM, 4.9 GB GPU  | extracts person names, names of locations, organizations from uncased text using ruBert-based (pyTorch) model                                                                                |
| Sentseg                | 2.4 GB RAM, 4.9 GB GPU  | recovers punctuation using ruBert-based (pyTorch) model and splits into sentences                                                                                                            |
| Spacy Annotator        | 250 MB RAM              | token-wise annotations by Spacy                                                                                                                                                              |
| Spelling Preprocessing | 8 GB RAM                | Russian Levenshtein correction model                                                                                                                                                         |
| Toxic Classification   | 3.5 GB RAM, 3 GB GPU    | Toxic classification model from Transformers specified as PRETRAINED_MODEL_NAME_OR_PATH                                                                                                      |
| Wiki Parser            | 100 MB RAM              | extracts Wikidata triplets for the entities detected with Entity Linking                                                                                                                     |
| DialogRPT              | 3.8 GB RAM,  2 GB GPU   | DialogRPT model which is based on [Russian DialoGPT by DeepPavlov](https://huggingface.co/DeepPavlov/rudialogpt3_medium_based_on_gpt2_v2) and fine-tuned on Russian Pikabu Comment sequences |

## Skills & Services
| Name                 | Requirements             | Description                                                                                                                         |
|----------------------|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| DialoGPT             | 2.8 GB RAM, 2 GB GPU     | [Russian DialoGPT by DeepPavlov](https://huggingface.co/DeepPavlov/rudialogpt3_medium_based_on_gpt2_v2)                             |
| Dummy Skill          |                          | a fallback skill with multiple non-toxic candidate responses and random Russian questions                                           |
| Personal Info Skill  | 40 MB RAM                | queries and stores user's name, birthplace, and location                                                                            |
| DFF Generative Skill | 50 MB RAM                | **[New DFF version]** generative skill which uses DialoGPT service to generate 3 different hypotheses                               |
| DFF Intent Responder | 50 MB RAM                | provides template-based replies for some of the intents detected by Intent Catcher annotator                                        |
| DFF Program Y Skill  | 80 MB RAM                | **[New DFF version]** Chatbot Program Y (https://github.com/keiffster/program-y) adapted for Dream socialbot                        |
| DFF Friendship Skill | 70 MB RAM                | **[New DFF version]** DFF-based skill to greet the user in the beginning of the dialog, and forward the user to some scripted skill |
| DFF Template Skill   | 50 MB RAM                | **[New DFF version]** DFF-based skill that provides an example of DFF usage                                                         |
| Text QA              | 3.8 GiB RAM, 5.2 GiB GPU | Навык для ответа на вопросы по тексту.                                                                                              |



# Публикации

### Alexa Prize 3
[Kuratov Y. et al. DREAM technical report for the Alexa Prize 2019 //Alexa Prize Proceedings. – 2020.](https://m.media-amazon.com/images/G/01/mobile-apps/dex/alexa/alexaprize/assets/challenge3/proceedings/Moscow-DREAM.pdf)

### Alexa Prize 4
[Baymurzina D. et al. DREAM Technical Report for the Alexa Prize 4 //Alexa Prize Proceedings. – 2021.](https://d7qzviu3xw2xc.cloudfront.net/alexa/alexaprize/docs/sgc4/MIPT-DREAM.pdf)


# License

DeepPavlov Dream is licensed under Apache 2.0.

Program-y (see `dream/skills/dff_program_y_skill`, `dream/skills/dff_program_y_wide_skill`, `dream/skills/dff_program_y_dangerous_skill`) 
is licensed under Apache 2.0.
Eliza (see `dream/skills/eliza`) is licensed under MIT License.


## Report creating
For making certification `xlsx` - file with bot responses, you can use `xlsx_responder.py` script by executing
```shell
docker-compose -f docker-compose.yml -f dev.yml exec -T -u $(id -u) agent python3 \
        utils/xlsx_responder.py --url http://0.0.0.0:4242 \
        --input 'tests/dream/test_questions.xlsx' \
        --output 'tests/dream/output/test_questions_output.xlsx'\
      --cache tests/dream/output/test_questions_output_$(date --iso-8601=seconds).json
```
Make sure all services are deployed. `--input` - `xlsx` file with certification questions, `--output` - `xlsx` file with bot responses, `--cache` - `json`, that contains a detailed markup and is used for a cache.
