#!/bin/bash

docker-compose -f docker-compose.yml -f assistant_dists/dream_bot_kg_prompted/docker-compose.override.yml -f assistant_dists/dream_bot_kg_prompted/dev.yml -p bot_test up -d terminusdb-server bot-knowledge-memorizer
sleep 30
python annotators/bot_knowledge_memorizer/test.py
docker-compose -f docker-compose.yml -f assistant_dists/dream_bot_kg_prompted/docker-compose.override.yml -f assistant_dists/dream_bot_kg_prompted/dev.yml -p bot_test down