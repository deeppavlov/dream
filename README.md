# DeepPavlov Dream

**DeepPavlov Dream** is a platform for creating multi-skill chatbots.

To get architecture documentation, please refer to DeepPavlov Agent [readthedocs documentation](https://deeppavlov-agent.readthedocs.io).


# Distributions

We've already included two distributions: Deepy and a full-sized Dream chatbot.


# Quick Start

### Deploying via proxy
The easiest way to try out Dream is to deploy it via proxy.
This way all the requests will be redirected to DeepPavlov API, so you don't have to use any local resources.

1. Clone the repo

   ```git clone https://github.com/deepmipt/dream```


2. Install [docker](https://docs.docker.com/engine/install/) and [docker-compose](https://docs.docker.com/compose/install/) 

   If you get a "Permission denied" error running docker-compose, make sure to [configure your docker user](https://docs.docker.com/engine/install/linux-postinstall/) correctly.


3. Run

   ```docker-compose -f docker-compose.yml -f dev.yml -f proxy.yml up --build```

   - `docker-compose.yml` is your main deployment configuration;

   - `dev.yml` includes volume bindings for easier debugging;

   - `proxy.yml` is a list of proxied containers. See [proxy usage](#proxy-usage).


### Deploying components locally

Any components included in `docker-compose.yml` and not included in `proxy.yml` will be deployed locally.
Depending on your needs, you can:
   - Run ```docker-compose up --build``` to deploy everything on your machine.
   - Remove the components you need to deploy locally from `proxy.yml` and run
   
      ```docker-compose -f docker-compose.yml -f proxy.yml up --build```.

**Please note, that DeepPavlov Dream components require a lot of resources.**
Refer to the [components](#components) section to see estimated requirements for each component.



# Proxy usage

If your deployment resources are limited, you can replace containers with their proxied copies hosted by DeepPavlov.
To do this, override those container definitions inside `proxy.yml`, e.g.:
```
convers-evaluator-annotator:
  command: ["nginx", "-g", "daemon off;"]
  build:
    context: dp/proxy/
    dockerfile: Dockerfile
  environment:
    - PROXY_PASS=lnsigo.mipt.ru:8004
    - PORT=8004
```
and include this config in your deployment command:
```
docker-compose -f docker-compose.yml -f proxy.yml up --build
```
By default, `proxy.yml` contains all available proxy definitions.


# Components
## Annotators

| Name                    | Requirements | Description |
|-------------------------| --- |-------------| 
| Spelling preprocessing  | req | desc        |
| Sentseg                 | req | desc        |
| Spacy nounphrases       | req | desc        |
| Conceptnet              | req | desc        |
| Badlisted words         | req | desc        |
| ASR                     | req | desc        |
| Factoid classification  | req | desc        |
| Intent catcher          | req | desc        |
| Fact random             | req | desc        |
| Fact retrieval          | req | desc        |
| NER                     | req | desc        |
| Entity detection        | req | desc        |
| KBQA                    | req | desc        |
| Entity linking          | req | desc        |
| Wiki parser             | req | desc        |
| Sentrewrite             | req | desc        |
| Midas classification    | req | desc        |
| Combined classification | req | desc        |
| Entity sorter           | req | desc        |
| News API annotator      | req | desc        |
| Topic recommendation    | req | desc        |
| User persona extractor  | req | desc        |

## Skills
| Name                    | Requirements | Description |
|-------------------------| --- |-------------| 
| DFF Sports skill        | req | desc        |
| Eliza                   | req | desc        |
| Program Y               | req | desc        |
| Personality Catcher     | req | desc        |
| Intent Responder        | req | desc        |
| Dummy Skill             | req | desc        |
| Dummy Skill Dialog      | req | desc        |
| Misheard ASR            | req | desc        |
| DFF Movie skill         | req | desc        |
| Emotion skill           | req | desc        |
| Convert Reddit          | req | desc        |
| Personal Info skill     | req | desc        |
| DFF Coronavirus skill   | req | desc        |
| DFF Weather skill       | req | desc        |
| DFF Short Story skill   | req | desc        |
| Meta Script skill       | req | desc        |
| Short Story skill       | req | desc        |
| Small Talk skill        | req | desc        |
| Game Cooperative skill  | req | desc        |
| Program Y Wide          | req | desc        |
| News API skill          | req | desc        |
| Comet Dialog skill      | req | desc        |
| DFF Grounding skill     | req | desc        |
| Factoid QA              | req | desc        |
| DFF Animals skill       | req | desc        |
| DFF Gaming skill        | req | desc        |
| DFF Friendship skill    | req | desc        |
| Knowledge Grounding skill | req | desc        |
| DFF Travel skill        | req | desc        |
| DFF Food skill          | req | desc        |
| DFF Science skill       | req | desc        |
| DFF Music skill         | req | desc        |
| DFF Funfact skill       | req | desc        |
| DFF Gossip skill        | req | desc        |
| DFF Bot Persona skill   | req | desc        |
| DFF Wiki skill          | req | desc        |
| DFF Book skill          | req | desc        |
| DFF Art skill           | req | desc        |


# Papers
### Alexa Prize 3
[Kuratov Y. et al. DREAM technical report for the Alexa Prize 2019 //Alexa Prize Proceedings. – 2020.](https://m.media-amazon.com/images/G/01/mobile-apps/dex/alexa/alexaprize/assets/challenge3/proceedings/Moscow-DREAM.pdf)

### Alexa Prize 4
[Baymurzina D. et al. DREAM Technical Report for the Alexa Prize 4 //Alexa Prize Proceedings. – 2021.](https://d7qzviu3xw2xc.cloudfront.net/alexa/alexaprize/docs/sgc4/MIPT-DREAM.pdf)


# License

DeepPavlov Dream is licensed under Apache 2.0.


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