### Requirements

- configure aws cli: https://aws.amazon.com/ru/cli/
- configure aws lambda & ASK: https://developer.amazon.com/en-US/docs/alexa/custom-skills/host-a-custom-skill-as-an-aws-lambda-function.html#create-a-lambda-function-from-scratch
- Не забудь в веб-интерфейсе настроить имена хандлеров и интеграцию с Алексой
- У лямбды можно настроить свой таймаут, сейчас поставлен 10 сек для отладки
- лямбда смотрит в .env файлы, в них должны быть DP_AGENT_URL, DP_AGENT_PORT, SENTRY_DSN, и параметры для A/B тестов (опционально)

### Lambdas
- dp_agent_proxy_lambda - для прод
- dp_agent_proxy_lambda_dev - для staging
- все логи в CloudWatch


### Как деплоить лямбду

- Не забыть настроить aws cli
- Из корня dp-agent надо запустить скрипт deploy.sh: 
  - `aws_lambda/deploy.sh TARGET=target`, где target одно из ['dev', 'prod']
  - or `aws_lambda/deploy.sh LAMBDA_NAME=LAMBDA_NAME`
- Смотри, чтобы название функции LAMBDA_NAME (сейчас dp_agent_lambda_proxy) совпадало с названием лямбды в AWS
