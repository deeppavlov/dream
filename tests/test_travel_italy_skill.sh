#!/bin/bash

docker-compose -f docker-compose.yml -f assistant_dists/dream_kg/docker-compose.override.yml -f assistant_dists/dream_kg/dev.yml -p bot_test up --build -d
sleep 50
python skills/dff_travel_italy_skill/tests/test_response.py
sleep 10
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg/docker-compose.override.yml -f assistant_dists/dream_kg/dev.yml -p bot_test down