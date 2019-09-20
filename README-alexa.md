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
1. Открыть ssh туннель к докер менеджеру `ssh -i ~/Downloads/dream-local-idris-2.pem -NL localhost:2374:/var/run/docker.sock docker@ec2-18-232-102-32.compute-1.amazonaws.com`
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