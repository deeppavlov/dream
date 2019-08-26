# Alexa skill based on DeepPavlov Agent

CoBotQA miniskill
========================
CoBotQA miniskill sends requests to CoBot's services. Two environment variables
should be set to use this miniskill:
 * COBOT_API_KEY - API key given to our Team
 * COBOT_QA_SERVICE_URL - service url, could be found in Trello

 .env file
 =======================

 В корне нужно сделать .env файл со следующими полями. Значения полей ищи в Trello.

 ```
 EXTERNAL_FOLDER=/path
 COBOT_API_KEY=apikey
 COBOT_QA_SERVICE_URL=url
 # optional, only if you want to use docker-compose with `-f telegram.yml`
 TELEGRAM_TOKEN=token
 TELEGRAM_PROXY=proxy
 ```

How to run and test
=======================

```
$: docker-compose -f docker-compose.yml -f skills.yml -f dev.yml up --build
$: docker-compose -f docker-compose.yml -f skills.yml -f dev.yml exec agent bash
$(inside docker): python3 -m core.run
```


Deploy to staging
=======================

- новые .env переменные надо не забывать добавлять в .env.staging

1. Надо поставить себе docker-machine: https://docs.docker.com/machine/install-machine/

`base=https://github.com/docker/machine/releases/download/v0.16.0 &&
  curl -L $base/docker-machine-$(uname -s)-$(uname -m) >/tmp/docker-machine &&
  sudo mv /tmp/docker-machine /usr/local/bin/docker-machine`

Подробнее о docker-machine: https://docs.docker.com/machine/overview/

2. Сконфигурировать staging env (это надо проделывать только 1 раз):
```
➜  docker-machine create \       
--driver generic \
--generic-ip-address=10.11.1.75 \    
--generic-ssh-port 2275 \
--generic-ssh-user admin \
--generic-ssh-key ~/.ssh/id_rsa \
staging
```

3. Сделать так чтобы докер работал с удаленным демоном: `eval $(docker-machine env staging)`
4. Билдим сервисы `docker-compose -f docker-compose.yml -f skills.yml -f telegram.yml -f staging.yml build`
5. Запушить сервисы в докер регистри на удаленной машине `➜ docker-compose -f docker-compose.yml -f skills.yml -f telegram.yml -f staging.yml push`
6. Деплой на стейджинг: `docker stack deploy --compose-file docker-compose.yml,skills.yml,telegram.yml,staging.yml alexa_staging`

**Комментарии:**
- Создание своего докер регистри: `docker service create --name registry --publish published=5000,target=5000 registry:2`
- Какие порты надо открыть для докер и докер-машины: https://www.digitalocean.com/community/tutorials/how-to-configure-the-linux-firewall-for-docker-swarm-on-ubuntu-16-04
- Вот так можно создать окружение для стейджинга на удаленной машине используя docker-machine: https://dev.to/zac_siegel/using-docker-machine-to-provision-a-remote-docker-host-1267
- Unset docker-machine env: `eval "$(docker-machine env -u)"`
