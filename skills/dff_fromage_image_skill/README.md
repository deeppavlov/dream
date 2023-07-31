# dff-fromage-image-skill

## Description

**dff-fromage-image-skill** is a simple service that can discuss images

## Quickstart from docker

```bash
# create local.yml
python utils/create_local_yml.py -s dff-fromage-image-skill
# build service
docker-compose -f docker-compose.yml -f local.yml up -d --build dff-fromage-image-skill
# run tests
docker-compose -f docker-compose.yml -f local.yml exec dff-fromage-image-skill bash test.sh
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
* RAM: 1024 MB
