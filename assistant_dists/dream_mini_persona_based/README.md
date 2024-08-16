### Run distro

- proxy
```bash
docker-compose -f docker-compose.yml -f assistant_dists/dream_mini_persona_based/docker-compose.override.yml -f assistant_dists/dream_mini_persona_based/dev.yml -f assistant_dists/dream_mini_persona_based/proxy.yml up --build
```

- locally
```bash
docker-compose -f docker-compose.yml -f assistant_dists/dream_mini_persona_based/docker-compose.override.yml -f assistant_dists/dream_mini_persona_based/dev.yml up --build
```

### chat with distro

```bash
docker-compose exec agent python -m deeppavlov_agent.run agent.channel=cmd agent.pipeline_config=assistant_dists/dream_mini_persona_based/pipeline_conf.json
```