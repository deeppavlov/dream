# Program-Y
Program-Y is a fully compliant AIML 2.1 rolebased chatbot based on [Program-Y](https://github.com/keiffster/program-y/wiki) framework written in Python 3.

# Quickstart from docker 

```bash
docker build -t ${SERVICE_DOCKER_IMAGE} --build-arg SERVICE_NAME=${SERVICE_NAME} --build-arg RANDOM_SEED=${RANDOM_SEED} --build-arg SERVICE_PORT=${SERVICE_PORT} --file skills/${SERVICE_NAME}/Dockerfile .
docker run -d --rm ${SERVICE_DOCKER_IMAGE}
```

# Average RAM for CPU and average starting time
Average RAM usage ~ 706 MiB
Average starting time ~ 16 seconds
Average request execution time ~ 64 μs
