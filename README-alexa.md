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
To run on GPU & optimized for performance configuration:\
```
$: docker-compose -f docker-compose.yml -f dev.yml up --build
```

To run on single machine without GPU:
```
$: docker-compose -f docker-compose.yml -f dev.yml -f cpu.yml -f one_worker.yml up --build
```

To run lightweight version with all sevices except agent and mongo running on MIPT cluster:
```
$: docker-compose -f docker-compose.yml -f dev.yml -f proxy.yml up --build
```

Если был изменён какой-то сервис и ты хочешь его отлаживать, убери этот сервис из proxy.yml (не закоммить случайно).
Можено ещё добавить этот сервис в свой локальный .yml (по образу и подобию docker-compose.yml) и добавить `-f твой.yml`
после `-f proxy.yml`.

Run agent:
```
$: docker-compose -f docker-compose.yml -f dev.yml exec agent bash
$(inside docker): python -m deeppavlov_agent.run
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

Deploy to prod and staging
=======================

- новые ENV переменные надо не забывать добавлять в .env.staging, .env.dev и .env.prod.

1. Обновить код:
    - для staging: `git checkout dev; git pull origin dev`
    - для prod: `git fetch --tags; git checkout RELEASE_VERSION`
2. Деплой
    - одной командой: `./deploy.sh MODE=[all, agent, lambda] TARGET=[dev, prod]`
    - руками:
        1. Билдим и пушим образы в ECR: `VERSION="$(git rev-parse --short HEAD)" ENV_FILE=.env.prod DOCKER_REGISTRY=807746935730.dkr.ecr.us-east-1.amazonaws.com ./push_to_ecr.sh`
        2. Деплой на стейджинг `VERSION="$(git rev-parse --short HEAD)" ENV_FILE=.env.staging DOCKER_REGISTRY=807746935730.dkr.ecr.us-east-1.amazonaws.com DOCKER_HOST=localhost:2375 docker stack deploy --compose-file docker-compose.yml,staging.yml --with-registry-auth dream_staging`
        2. Деплой на прод: `VERSION="$(git rev-parse --short HEAD)" ENV_FILE=.env.prod DOCKER_REGISTRY=807746935730.dkr.ecr.us-east-1.amazonaws.com DOCKER_HOST=localhost:2374 docker stack deploy --compose-file docker-compose.yml,staging.yml --with-registry-auth dream_prod`

- Открыть ssh туннель к докер менеджеру `ssh -i ~/Downloads/dream-local-idris-2.pem -NL localhost:2374:/var/run/docker.sock docker@ec2-34-207-206-65.compute-1.amazonaws.com`
- Авторизация в ECR (если до этого не был запущен `./push_to_ecr`): `eval $(aws ecr get-login --no-include-email)`

**Комментарии:**
- pem ключ лежит тут https://trello.com/c/vEUbMmKK (не забудь `chmod 400`)
- https://docs.docker.com/docker-for-aws/deploy/
- Staging DOCKER_HOST port 2375
- Prod DOCKER_HOST port 2374
- Check if remote docker connection ok `DOCKER_HOST=localhost:2374 docker info`
- Посмотреть как там стек `DOCKER_HOST=localhost:2374 docker stack ps dream_staging`
- Посмотреть сервиса стека `DOCKER_HOST=localhost:2374 docker stack services dream_staging`
- Mongo user - https://devops.ionos.com/tutorials/enable-mongodb-authentication/
- Mongo сейчас на отдельной машине (TODO бэкапы)
- DefaultDNSTarget (output в CloudFormation) Prod: `Docker-ExternalLoa-LOFSURITNPLE-525614984.us-east-1.elb.amazonaws.com`
- DefaultDNSTarget (output в CloudFormation) Staging: `Docker-st-External-1918W05RU8XQW-178993125.us-east-1.elb.amazonaws.com`
- Ports exposed with --publish are automatically exposed through the platform load balancer


Deploy Machine
=======================
Поднята деплой машина на амазоне. Через нее можно быстро собрать и запушить имейджи в регистри и сделать деплой.

- `ssh -i ~/Downloads/dream-local-idris.pem ubuntu@34.203.223.60`
- aws сконфигурирован
- Скачать репу можно в папку `/home/ubuntu/dp-agent-alexa`


GPU
========================
1. Create machine with public ip with GPU AMI
2. Setup docker daemon to use nvidia runtime as default and couldwatch logging:
```
/etc/docker/daemon.json:
{
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
   "default-runtime": "nvidia",
    "log-driver": "awslogs",
    "log-opts": {
        "awslogs-group": "Docker-staging-lg",
        "tag": "{{.Name}}-{{.ID}}"
    }
}
# or "awslogs-group": "Docker-lg" for prod!!!
```
3. Restart docker daemon and check it (`sudo service docker restart`)
```
ubuntu@ip-172-31-42-16:~$ sudo nano /etc/docker/daemon.json
ubuntu@ip-172-31-42-16:~$ sudo service docker stop
ubuntu@ip-172-31-42-16:~$ sudo service docker start
ubuntu@ip-172-31-42-16:~$ sudo service docker status
ubuntu@ip-172-31-42-16:~$ docker run nvidia/cuda:9.0-base nvidia-smi
```
4. Add GPU worker to docker swarm
5. Find docker gpu node in docker manager: `docker node ls`
5. Add label to the GPU worker machine `docker node update --label-add with_gpu=true o0mvol5rehp80k9a0xkzye7zw`
6. Add IAM role Docker-staging-WorkerInstanceProfile (Docker-WorkerInstanceProfile for prod) to EC2 instance Actions -> Instance setting -> Attach/Replace IAM Role

You can run to check if logs appear in cloudwatch by command `docker run alpine echo 'Say Hi!'`
7. Setup placement in docker-compose.yml.

- For local setup install nvidia-docker2 https://github.com/NVIDIA/nvidia-docker/wiki/Installation-(version-2.0)
- Restart docker daemon and do step 2.

How to run monitoring script
==========================
- `SENTRY_DSN=https://512146d297934039b6e98c9388701f4a@o488460.ingest.sentry.io/5548871 python3 service_monitoring.py http://Docker-ExternalLoa-LOFSURITNPLE-525614984.us-east-1.elb.amazonaws.com:4242`

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


Миграции
==========================

1. Открыть туннель к Монго Машине на Амазоне: `ssh -i ~/Downloads/dream-local-idris.pem -L 27018:localhost:27017 ubuntu@18.208.199.52 -N`
2. Выполнить скрипт миграции: `python -m utils.migrate --host localhost --port 27018 -od dream-staging -nd dream-staging-v2-111119`, где -od - название текущей базы, -nd - название базы после миграции.
3. Поменять DB_NAME в .env файле - `DB_NAME=dream-staging-v2-111119`

Инфраструктура
==============

- setup cron to prune docker images on all machines: `0 3 * * * /usr/bin/docker system prune -f -a`
- make sure that cron daemon is running: `ps -ef | grep cron | grep -v grep`
- setup service to remove stopped containers: `docker --host $DOCKER_HOST service create -d --name docker-rm --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock --mode=global --restart-condition none --update-parallelism 0 --update-failure-action continue docker /bin/sh -c "docker rm \$(docker ps -q -a); exit 0;"`

A/B тесты
=========
Чтобы запустить A/B тесты нужно создать ветку под A/B тест с:

1. В .env.prod задать переменными окружения `A_VERSION`, `A_AGENT_URL`, `A_AGENT_PORT`, `B_VERSION`, `B_AGENT_URL`, `B_AGENT_PORT`. Смотри пример в `.end.prod_ab_tests_example`. Доля трафика между версиями регулируется с помощью переменных A : B = `A_VERSION_RATIO` : `B_VERSION_RATIO`. В версиях поддерживаются только теги (не коммиты, не ветки).
2. Убедиться, что в версиях для тестирования в `.env.prod` нет конфигурации A/B тестов.
3. Запушить ветку и перейти в нее на машине, с которой будут деплоится A/B тесты.
4. Если A/B тесты деплоятся на prod кластер, на котором сейчас запущены A/B тесты, то запустить `./deploy_ab_tests.sh`
5. Если A/B тесты деплоятся на prod кластер, на котором сейчас запущена одна релизная версия, то сначала надо снести `dream_prod` стак (через портейнер или `DOCKER_HOST=localhost:2374 docker stack rm dream_prod`) и перенаправить трафик на staging. Потом запустить `./deploy_ab_tests.sh` с закомментированными строками 50, 56 -- деплой версии A на staging (todo: если есть прод стак, то удалять его после деплоя A на staging).
6. Если после A/B тестов нужно запустить одну релизную версию, то надо сначала снести стаки A/B тестов и перенаправить трафик на staging и запустить `./deploy.sh MODE=all TARGET=prod`.

Версия пишется в аттрибуты `human_utterances`.

Нагрузочные тесты
=================
Чтобы запустить нагрузочное тестирование:

- устанавливаем в своё виртуальное окружение locust с `pip install locust`
- заходим в utils и выполняем `locust -f load_test.py -P 9000`. Параметр `-P` определяет порт на котором будет запущен сервис
- открываем в браузере `http://0.0.0.0:9000`
- Заполняем все поля, запускаем тестирование