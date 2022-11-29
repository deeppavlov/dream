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
[Russian DialoGPT модели](https://huggingface.co/Grossmend/rudialogpt3_medium_based_on_gpt2). 
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

## Аннотаторы (Annotators)

| Name                   | Requirements             | Description                                                                                                                                                                                                   |
|------------------------|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Badlisted words        | 50 MiB RAM               | Аннотатор детекции нецензурных слов основан на лемматизации с помощью pymorphy2 и проверки по словарю нецензурных слов.                                                                                       |
| Entity Detection       | 3 GiB RAM                | Аннотатор извлечения не именованных сущностей и определения их типа для русского языка нижнего регистра на основе на основе нейросетевой модели ruBERT (PyTorch).                                             |
| Entity Linking         | 300 MiB RAM              | Аннотатор связывания (нахождения Wikidata id) сущностей, извлеченных с помощью Entity detection, на основе дистиллированной модели ruBERT.                                                                    |
| Intent Catcher         | 1.8 GiB RAM, 5 Gib GPU   | Аннотатор детектирования специальных намерений пользователя на основе многоязычной модели Universal Sentence Encoding.                                                                                        |
| NER                    | 1.8 GiB RAM, 5 Gib GPU   | Аннотатор извлечения именованных сущностей для русского языка нижнего регистра на основе нейросетевой модели Conversational ruBERT (PyTorch).                                                                 |
| Sentseg                | 2.4 GiB RAM, 5 Gib GPU   | Аннотатор восстановления пунктуации для русского языка нижнего регистра на основе нейросетевой модели ruBERT (PyTorch). Модель обучена на русскоязычных субтитрах.                                            |
| Spacy Annotator        | 250 MiB RAM              | Аннотатор токенизации и аннотирования токенов на основе библиотеки spacy и входящей в нее модели “ru_core_news_sm”.                                                                                           |
| Spelling Preprocessing | 4.5 GiB RAM              | Аннотатор исправления опечаток и грамматических ошибок на основе модели расстояния Левенштейна. Используется предобученная модель из библиотеки DeepPavlov.                                                   |
| Toxic Classification   | 1.9 GiB RAM, 1.3 Gib GPU | Классификатор токсичности для фильтрации реплик пользователя [от Сколтеха](https://huggingface.co/SkolkovoInstitute/russian_toxicity_classifier)                                                              |
| Wiki Parser            | 100 MiB RAM              | Аннотатор извлечения триплетов из Wikidata для сущностей, извлеченных с помощью  Entity detection.                                                                                                            |
| DialogRPT              | 3.9 GiB RAM, 2.2 GiB GPU |  Сервис оценки вероятности реплики понравиться пользователю (updown) на основе ранжирующей модели DialogRPT, которая дообучена на основе генеративной модели Russian DialoGPT на комментариев с сайта Пикабу. |

## Навыки и Сервисы (Skills & Services)
| Name                 | Requirements              | Description                                                                                                                                                                   |
|----------------------|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DialoGPT             | 2.8 GiB RAM, 2.2 GiB GPU  | Сервис генерации реплики по текстовому контексту диалога на основе предобученной модели Russian [DialoGPT](https://huggingface.co/Grossmend/rudialogpt3_medium_based_on_gpt2) |
| Dummy Skill          | a part of agent container | Навык для генерации ответов-заглушек и выдачис лучайных вопросов из базы в каечстве linking-questions.                                                                        |
| Personal Info Skill  | 40 MiB RAM                | Сценарный навык для извлечения и запоминания основной личной информации о пользователе.                                                                                       |
| DFF Generative Skill | 50 MiB RAM                | **[New DFF version]** навык, выдающий 5 гипотез, выданных сервисом DialoGPT                                                                                                   |
| DFF Intent Responder | 50 MiB RAM                | **[New DFF version]** Сценарный навык на основе DFF для ответа на специальные намерения пользователя.                                                                         |
| DFF Program Y Skill  | 80 MiB RAM                | **[New DFF version]** Сценарный навык на основе DFF для ответа на общие вопросы в виде AIML компоненты.                                                                       |
| DFF Friendship Skill | 70 MiB RAM                | **[New DFF version]** Сценарный навык на основе DFF приветственной части диалога с пользователем.                                                                             |


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
