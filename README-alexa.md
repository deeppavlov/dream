# Alexa skill based on DeepPavlov Agent

CoBotQA miniskill
========================
CoBotQA miniskill sends requests to CoBot's services. Two environment variables
should be set to use this miniskill:
 * COBOT_API_KEY - API key given to our Team
 * COBOT_QA_SERVICE_URL - service url, could be found in Trello

 .env.dev .env.staging files
 =======================

 - новые ENV переменные надо не забывать добавлять в .env.staging и .env.dev

How to run and test
=======================

```
$: docker-compose -f docker-compose.yml -f dev.yml up --build
$: docker-compose -f docker-compose.yml -f dev.yml exec agent bash
$(inside docker): python3 -m core.run
```

Автотесты
====================
по умолчанию все тесты запускаются на gpu: `tests/runtests.sh`

запуск на cpu: `tests/runtests.sh DEVICE=cpu`
запуск определенных тестов с параметром MODE:
- тестовый диалог: `tests/runtests.sh MODE=test_dialog`
- получить ответы бота на спорные/фактоидные/персона вопросы `tests/runtests.sh MODE=infer_questions`


Кодстиль
====================
`bin/run_codestyle.sh`

#### Про использование generate_composefile

- НЕ НАДО ЕГО ИСПОЛЬЗОВАТЬ!

```
generate_composefile.py лежит в билиотеке для непродвинутых пользователей, которые просто хотят что-то поднять из коробки.
У нас docker-compose.yml уже сгенерирован и поэтому запускать generate_composefile.py без надобности не нужно.
Запускайте его (хотя можно и вручную в docker-compose.yml добавить), когда добавляете или изменяете internal скилл в config.py.
Причем обращайте внимание на следующие вещи:
- Секции volumes и env_file в docker-compose.yml не должно быть. Сейчас volumes и env_file описываются в файлах staging.yml и dev.yml.
```

Deploy to staging
=======================

- новые .env переменные надо не забывать добавлять в .env.staging и .env.dev

0. Билдим и пушим образы в ECR: `DOCKER_REGISTRY=807746935730.dkr.ecr.us-east-1.amazonaws.com ./push_to_ecr.sh`
1. Открыть ssh туннель к докер менеджеру `ssh -i ~/Downloads/dream-local-idris-2.pem -NL localhost:2374:/var/run/docker.sock docker@ec2-34-207-206-65.compute-1.amazonaws.com`
2. Авторизация в ECR (если до этого не был запущен `./push_to_ecr`): `eval $(aws ecr get-login --no-include-email)`
3. Деплой на стейджинг: `DOCKER_REGISTRY=807746935730.dkr.ecr.us-east-1.amazonaws.com DOCKER_HOST=localhost:2374 docker stack deploy --compose-file docker-compose.yml,staging.yml --with-registry-auth dream_staging`

**Комментарии:**
- pem ключ лежит тут https://trello.com/c/vEUbMmKK (не забудь `chmod 400`)
- Как поднять nginx , чтобы обращаться к http сервису агента: `DOCKER_REGISTRY=807746935730.dkr.ecr.us-east-1.amazonaws.com DOCKER_HOST=localhost:2374 docker service create --name nginx --publish published=80,target=4242 nginx`
- https://docs.docker.com/docker-for-aws/deploy/
- Check if remote docker connection ok `DOCKER_HOST=localhost:2374 docker info`
- Посмотреть как там стек `DOCKER_HOST=localhost:2374 docker stack ps dream_staging`
- Посмотреть сервиса стека `DOCKER_HOST=localhost:2374 docker stack services dream_staging`
- Mongo user - https://devops.ionos.com/tutorials/enable-mongodb-authentication/
- Mongo сейчас на отдельной машине (TODO бэкапы)
- DefaultDNSTarget (output в CloudFormation): `Docker-ExternalLoa-LOFSURITNPLE-525614984.us-east-1.elb.amazonaws.com`


Deploy to Alexa Lambda
=======================

- [Deploy to Alexa Lambda README](aws_lambda/README.md)


Deploy Machine
=======================
Поднята деплой машина на амазоне. Через нее можно быстро собрать и запуишть имейджи в регистри и сделать деплой.

- `ssh -i ~/Downloads/dream-local-idris.pem ubuntu@34.203.223.60`
- aws сконфигурирован
- Скачать репу можно в папку `/home/ubuntu/dp-agent-alexa`


GPU
========================
1. Create machine with public ip with GPU AMI
2. Setup docker daemon to use nvidia runtime as default
```
ubuntu@ip-172-31-42-16:~$ cat /etc/docker/daemon.json
{
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
   "default-runtime": "nvidia"
}
```
3. Restart docker daemon and check it
```
ubuntu@ip-172-31-42-16:~$ sudo nano /etc/docker/daemon.json
ubuntu@ip-172-31-42-16:~$ sudo service docker stop
ubuntu@ip-172-31-42-16:~$ sudo service docker start
ubuntu@ip-172-31-42-16:~$ sudo service docker status
ubuntu@ip-172-31-42-16:~$ docker run nvidia/cuda:9.0-base nvidia-smi
```
4. Add GPU worker to docker swarm
5. Add label to the GPU worker machine `docker node update --label-add with_gpu=true o0mvol5rehp80k9a0xkzye7zw`
6. Setup placement in docker-compose.yml.


- For local setup install nvidia-docker2 https://github.com/NVIDIA/nvidia-docker/wiki/Installation-(version-2.0)
- Restart docker daemon and do step 2.

How to run monitoring script
==========================
- `SENTRY_DSN=https://7a6d57df6fb44ae4bfc3d43a8b4f16f3@sentry.io/1553895 python3 service_monitoring.py http://Docker-ExternalLoa-LOFSURITNPLE-525614984.us-east-1.elb.amazonaws.com:4242`

- Для мониторинга CPU/Memory/Disk используется https://github.com/stefanprodan/swarmprom - Docker Swarm monitoring with Prometheus, Grafana, cAdvisor, Node Exporter, Alert Manager and Unsee.

- ssh to Deploy machine && cd /home/ubuntu/swarmprom && run command below:

```
ADMIN_USER=admin \
ADMIN_PASSWORD=dreamlocal \
SLACK_URL=https://hooks.slack.com/services/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 \
SLACK_CHANNEL=alexaprize-alerts \
SLACK_USER=alertmanager \
DOCKER_HOST=localhost:2374 \
docker stack deploy -c docker-compose.yml mon
```
