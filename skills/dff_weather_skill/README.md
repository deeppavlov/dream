# dff-weather-skill

## Description

**dff-weather-skill** is a service that can provide weather forecasts.

## Quickstart from docker

```bash
# create local.yml
python utils/create_local_yml.py -s dff-weather-skill
# build service
docker-compose -f docker-compose.yml -f local.yml up -d --build dff-weather-skill
# run tests
docker-compose -f docker-compose.yml -f local.yml exec dff-weather-skill bash test.sh
# run a dialog with the agent
docker-compose -f docker-compose.yml -f local.yml exec agent python -m deeppavlov_agent.run
```

## Quickstart without docker

```bash
pip install -r requirements.txt
gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}
```

## Resources

* Average execution time: ~150 ms
* Starting time: ~25 sec
* RAM: 1.3G
