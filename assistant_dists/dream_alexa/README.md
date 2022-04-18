## Deploy Dream Alexa
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_alexa/docker-compose.override.yml -f assistant_dists/dream_alexa/dev.yml -f assistant_dists/dream_alexa/proxy.yml up --build
```
