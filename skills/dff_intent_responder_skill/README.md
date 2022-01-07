# dff-intent-responder-skill

## Description

**dff-intent-responder-skill** is a skill to exit the dialogue. There are only answers here, phrases for leaving the dialogue are detected in the ** IntentCatcher ** annotator.

## Quickstart from docker

```bash
# create local.yml
python utils/create_local_yml.py -s dff-intent-responder-skill
# build service
docker-compose -f docker-compose.yml -f local.yml up -d --build dff-intent-responder-skill
# run tests
docker-compose -f docker-compose.yml -f local.yml exec dff-intent-responder-skill bash test.sh
# run a dialog with the agent
docker-compose -f docker-compose.yml -f local.yml exec agent python -m deeppavlov_agent.run
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
