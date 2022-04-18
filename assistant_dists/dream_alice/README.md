## Deploy Dream Alice
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_alice/docker-compose.override.yml -f assistant_dists/dream_alice/dev.yml -f assistant_dists/dream_alice/proxy.yml up --build
```
