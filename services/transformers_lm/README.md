# Transformers LLM Service

## Description

Service for LLMs connection from HuggingFace transformers.

### Parameters

Parameter `PRETRAINED_MODEL_NAME_OR_PATH` defines which model to use. Supported models are:
- "EleutherAI/gpt-j-6B" (not available via proxy
- "OpenAssistant/pythia-12b-sft-v8-7k-steps" (available via Proxy)
- "togethercomputer/GPT-JT-6B-v1" (available via Proxy)
- "lmsys/vicuna-13b-v1.3" (not available via proxy)
- Any other, if one creates a new container with the considered model name and raise it locally.

## Dependencies

- When using via Proxy, depends on Proxy stability.


## How to Add a New Large Language Model from Transformers into DeepPavlov Dream?

If you want to integrate a new LLM from Transformers into DeepPavlov Dream Platform, follow the instruction below.
You may use the [pull-request with ruGPT-3.5 integration](https://github.com/deeppavlov/dream/pull/534) as an example 
of a new LLM integration to Universal Distributions.

1. Depending on the language of the LLM of interest, select either `universal_prompted_assistant` or 
`universal_ru_prompted_assistant` as a distribution to add an LLM to. Let's call the selected one Universal Assistant.
2. In `dream/components.tsv` reserve a port for a new component which will be named as `transformers-lm-modelname`.
3. In `docker-compose.override.yml` in `dream/assistant_dists/{Universal Assistant}` create a new container, name it
like `transformers-lm-modelname`. In particular:
   1. assign `PRETRAINED_MODEL_NAME_OR_PATH` to a name of the model from transformers to be integrated; 
   2. assign `SERVICE_PORT` (and its value in a command also) to a selected on the previos step; 
   3. assign `HALF_PRECISION` value to `1` if you want to use a model in a half precision mode (to save computational
   resources); 
   4. assign `SERVICE_NAME` to a `transformers_lm_modelname` (for the uniformity);
   5. include a new component to `WAIT_HOSTS` of the agent container;
   6. do not assign `CUDA_VISIBLE_DEVICES` to another value in this file -- you may utilize another `yml` files for it;
   7. You will get something like this:
   ```yaml
   transformers-lm-{modelname}:
    env_file: [ .env ]
    build:
      args:
        SERVICE_PORT: {selectedport}
        SERVICE_NAME: transformers_lm_{modelname}
        PRETRAINED_MODEL_NAME_OR_PATH: {modelnamefromtransfofmers}
        HALF_PRECISION: 1
      context: .
      dockerfile: ./services/transformers_lm/Dockerfile
    command: flask run -h 0.0.0.0 -p {selectedport}
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - FLASK_APP=server
    deploy:
      resources:
        limits:
          memory: {max RAM in G}G
        reservations:
          memory: {max RAM in G}G
   ```
4. In `dev.yml` in `dream/assistant_dists/{Universal Assistant}` assign volumes and ports mapping for your new model:
   1. for a container `transformers-lm-modelname` map the volumes:
   ```yaml
   volumes:
      - "./services/transformers_lm:/src"
      - "./common:/src/common"
      - "~/.deeppavlov/cache:/root/.cache"
   ```
   2. for a container `transformers-lm-modelname` map the ports:
   ```yaml
   ports:
      - {selectedport}:{selectedport}
   ```
5. Add a new container to `cpu.yml`, if necessary.
6. If you are a DeepPavlov employee, have access to DeepPavlov's computational resources, and want to create a proxy
for a new model, follow the steps:
   1. run a new container on the same server where all other proxied containers are built.
   2. add a new container to a `proxy.yml` 
   ```yaml
   transformers-lm-{modelname}:
    command: ["nginx", "-g", "daemon off;"]
    build:
      context: dp/proxy/
      dockerfile: Dockerfile
    environment:
      - PROXY_PASS=proxy.deeppavlov.ai:{selectedport}
      - PORT={selectedport}
    ```
7. Using Universal Assistant, one may assign generation parameters in the request body. But default parameters for a new
model must be provided anyway. Create and fill a configuration file with parameters in 
folder `dream/common/generative_configs/`. 
8. Add a new model to be considered in the universal skill in `dream/skills/dff_universal_prompted_skill/scenario/response.py`
in a dictionary `ENVVARS_TO_SEND` with a mapping to considered environmental variables to send to a LLM (for example,
for sending API keys) as follows:
```python
    "http://transformers-lm-{modelname}:{selectedport}/respond": [],
```
9. Add a new model to a `dream/MODELS.md` file for storing all the important info.
10. Now create a component cards required for `dreamtools` work:
    1. Create a file in `dream/components/` folder, fill it in the same way as for `components/vdfjkhg934nflgeafgv.yml`.
    2. Create a folder `dream/services/transformers_lm/service_configs/transformers-lm-{modelname}`, create two files
    `environment.yml` and `service.yml` in the same way as for
    `services/transformers_lm/service_configs/transformers-lm-rugpt35/service.yml` and 
    `services/transformers_lm/service_configs/transformers-lm-rugpt35/environment.yml`.