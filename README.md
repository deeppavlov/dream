# DeepPavlov Dream

**DeepPavlov Dream** is a platform for creating multi-skill chatbots.

Please refer to our [readthedocs documentation](https://deeppavlov-agent.readthedocs.io).

- [Alexa Bot README](README-alexa.md)
- Travis Tests Status on dev branch: [![Build Status](https://travis-ci.com/sld/dp-agent-alexa.svg?token=iYvsyXT3Gi1yjduLqC6t&branch=dev)](https://travis-ci.com/sld/dp-agent-alexa)
- Jenkins Tests Status on dev branch: [![Build Status](http://lnsigo.mipt.ru:8080/buildStatus/icon?job=assistant%2Fdev)](http://lnsigo.mipt.ru:8080/job/dp-multibranch/job/dev/)


# Distributions

We've already included two distributions: Deepy and a full-sized Dream chatbot.


# Quick Start

### Deploying via proxy
The easiest way to try out Dream is to deploy it via proxy.
This way all the requests will be redirected to DeepPavlov API, so you don't have to use any local resources.

1. Clone the repo

    ```git clone https://github.com/deepmipt/dream```

2. Run

    ```docker-compose -f docker-compose.yml -f dev.yml -f proxy.yml up --build```
    
    `dev.yml` includes volume bindings for easier debugging;

    `proxy.yml` is a list of proxied containers. See [proxy usage](#proxy-usage).


### Deploying components locally

Any components which are not included in `proxy.yml` will be deployed locally.


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
docker-compose -f docker-compose.yml -f proxy.yml up
```
By default, `proxy.yml` contains all available proxy definitions.   


# Components



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