# dff_template_skill

## Description

**dff_template_skill** is a skill to exit the dialogue. There are only answers here, phrases for leaving the dialogue are detected in the ** IntentCatcher ** annotator.

## Quickstart from docker

```bash
# create local.yml
python utils/create_local_yml.py -d assistant_dists/dream/ -s dff-template-skill
# build service
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/local.yml up -d --build dff-template-skill
# run tests
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/local.yml exec dff-template-skill bash test.sh
# check logs
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/local.yml logs -f dff-template-skill
# run a dialog with the agent
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/local.yml exec agent python -m deeppavlov_agent.run
```

## Quickstart without docker

```bash
pip install -r requirements.txt
gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}
```

## Resources

* Execution time: 46 ms
* Starting time: 1.5 sec
* RAM: 45 MB

## Change history
### Jan 8, 2022
The dialogue skill **skills\dff-intent-responder-skill** was created based on **skills\IntentResponder** service to refactor old code with the usage of the new dff framework. The new service repeats the previous service logic which is based on the intention detection from the payload of the inbound HTTP request. The intention from the latest human_utterances element with "detected"=1 and the highest confidence is selected and the appropriate response is created; the confidence value is sent to output without change. If no input intention is detected, then a default response with 'dont_understand' logic is sent.
### Jan 15, 2022
Tests for all input intentions including a default case are added.
### Jan 21, 2022
The dialogue skill **skills\dff-intent-responder-skill** is moved to **skills\dff_template_skill**. Code review changes applied, tests are recreated in microservice environment.
