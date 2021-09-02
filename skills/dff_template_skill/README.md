# dff-funfact-skill

## Description

**dff-funfact-skill** is a simple service that can give random or thematic fun facts.

## Quickstart from docker

```bash
docker build -t ${SERVICE_DOCKER_IMAGE} --build-arg SERVICE_NAME=${SERVICE_NAME} --build-arg RANDOM_SEED=${RANDOM_SEED} --build-arg SERVICE_PORT=${SERVICE_PORT} .
docker run -d --rm ${SERVICE_DOCKER_IMAGE}
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