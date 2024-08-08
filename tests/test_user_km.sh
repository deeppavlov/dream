#!/bin/bash

docker-compose -f docker-compose.yml -f assistant_dists/dream_kg_prompted/docker-compose.override.yml -f assistant_dists/dream_kg_prompted/dev.yml -p bot_test up -d terminusdb-server user-knowledge-memorizer-prompted
sleep 30
python annotators/user_knowledge_memorizer/test.py
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg_prompted/docker-compose.override.yml -f assistant_dists/dream_kg_prompted/dev.yml -p bot_test down