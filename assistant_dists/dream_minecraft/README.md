## Run distribution
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_minecraft/docker-compose.override.yml -f assistant_dists/dream_minecraft/dev.yml -f assistant_dists/dream_minecraft/proxy.yml up --build
```

## Rerun the minecraft connector
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_minecraft/docker-compose.override.yml -f assistant_dists/dream_minecraft/dev.yml -f assistant_dists/dream_minecraft/proxy.yml up --build minecraft minecraft-skill
```
