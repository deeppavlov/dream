# Пререквизиты для запуска:

1. Убедиться, что все сервисы верно определены в `dev.yml`, `proxy.yml`, `pipeline_conf.json`;
2. Убедиться, что порты для сервисов и скиллов уникальны, что порты, на которые ссылаются сервисы и скиллы — коррекнты;
3. Убедиться, что в docker-compose.override.yml установлено: `agent.channel=telegram agent.telegram_token=$TG_TOKEN`;
4. Убедиться, что в переменных среды установлен токен бота в телеграме с названием `$TG_TOKEN`.

# Команда для запуска:

```
docker-compose -f docker-compose.yml -f assistant_dists/dream_mint/docker-compose.override.yml -f \
assistant_dists/dream_mint/dev.yml -f assistant_dists/dream_mint/proxy.yml up --build --force-recreate; docker stop $(docker ps -aq)
```

Внимание! Последняя часть команды останавливает все запущенные на машине контейнеры. Если это не нужно, следует убрать часть команды после точки с запятой или отредактировать её так, чтобы она останавливала только некоторые контейнеры, если заранее известны их названия.