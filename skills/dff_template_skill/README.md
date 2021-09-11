# Program-Y

## Description

**Program-Y** is a fully compliant AIML 2.1 rolebased chatbot based on [Program-Y](https://github.com/keiffster/program-y/wiki) framework written in Python 3.

## Quickstart from docker

```bash
# create local.yml
python utils/create_local_yml.py -s program-y -s convers-evaluation-selector 
# build service
docker-compose -f docker-compose.yml -f local.yml up -d --build 
# run tests
docker-compose -f docker-compose.yml -f local.yml exec program-y bash test.sh
# run a dialog with the agent
docker-compose -f docker-compose.yml -f local.yml exec agent python -m deeppavlov_agent.run
```

## Quickstart without docker

```bash
pip install -r requirements.txt
gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}
```

## Resources

* Execution time: 0.064 ms
* Starting time: 16 sec
* RAM: 706 MB
