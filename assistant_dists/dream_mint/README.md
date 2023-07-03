# Prerequisites:

1. Make sure that all services are correctly defined in dev.yml, proxy.yml, pipeline_conf.json.
2. Ensure that the ports for services and skills are unique and that the ports referenced by services and skills are correct.
3. Verify that in docker-compose.override.yml, the following is set: agent.channel=telegram agent.telegram_token=$TG_TOKEN.
4. Ensure that the Telegram bot token is set in the environment variables as $TG_TOKEN.

# Launch command:

```
docker-compose -f docker-compose.yml -f assistant_dists/dream_mint/docker-compose.override.yml -f \
assistant_dists/dream_mint/dev.yml -f assistant_dists/dream_mint/proxy.yml up --build --force-recreate; docker stop $(docker ps -aq)
```

Attention! The last part of the command stops all running containers on the machine. If this is not required, remove the part of the command after the semicolon or edit it to stop only specific containers if their names are known in advance.