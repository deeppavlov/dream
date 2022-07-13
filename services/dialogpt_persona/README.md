GPU RAM = 1Gb
cpu time = 0.15 sec 
gpu time = 0.05 sec 

sudo docker-compose -f docker-compose.yml -f assistant_dists/dream_mini/docker-compose.override.yml -f assistant_dists/dream_mini/dev.yml -f assistant_dists/dream_mini/proxy.yml up --build

sudo docker-compose exec agent python -m deeppavlov_agent.run -pl assistant_dists/dream_mini/pipeline_conf.json
curl -d '{"key1":"value1", "key2":"value2"}' -H "Content-Type: application/json" -X POST http://localhost:8126/respond/