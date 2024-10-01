#!/bin/bash

pip install git+https://github.com/deeppavlov/custom_kg_svc.git@4c7dea8858c01fa11d10dbe3d528d91bf19555e2
docker-compose -f docker-compose.yml -f assistant_dists/dream_bot_kg_prompted/docker-compose.override.yml -f assistant_dists/dream_bot_kg_prompted/dev.yml -p bot_test up -d terminusdb-server
sleep 5
docker-compose -f docker-compose.yml -f assistant_dists/dream_bot_kg_prompted/docker-compose.override.yml -f assistant_dists/dream_bot_kg_prompted/dev.yml -p bot_test up --build -d bot-knowledge-memorizer
python annotators/bot_knowledge_memorizer/launch_time_test.py
python annotators/bot_knowledge_memorizer/test.py
docker-compose -f docker-compose.yml -f assistant_dists/dream_bot_kg_prompted/docker-compose.override.yml -f assistant_dists/dream_bot_kg_prompted/dev.yml -p bot_test down