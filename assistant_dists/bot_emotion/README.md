Run
```
docker-compose -f docker-compose.yml -f assistant_dists/bot_emotion/docker-compose.override.yml -f assistant_dists/bot_emotion/dev.yml -f assistant_dists/bot_emotion/proxy.yml up --build
```
providing ` --force-recreate` and/or `--remove-orphans` if necessary

Chat
```
docker-compose exec agent python -m deeppavlov_agent.run -pl assistant_dists/bot_emotion/pipeline_conf.json
```