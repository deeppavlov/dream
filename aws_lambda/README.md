### Requirements

- configure aws cli: https://aws.amazon.com/ru/cli/


### Как деплоить

- Не забыть настроить aws cli
- Из корня dp-agent надо запустить скрипт deploy.sh: 
  - `aws_lambda/deploy.sh TARGET=target`, где target одно из ['dev', 'prod']
  - or `aws_lambda/deploy.sh LAMBDA_NAME=LAMBDA_NAME`
- Смотри, чтобы название функции LAMBDA_NAME (сейчас dp_agent_lambda_proxy) совпадало с названием лямбды в AWS
- Таймаут 3 сек мало для тестов, надо увеличиваить
- Не забудь в веб-интерфейсе настроить имена хандлеров и интеграцию с Алексой
- *Тестовая lambda name:* dp_agent_lambda_proxy_test. Она использует skill-dream-dilyara.
