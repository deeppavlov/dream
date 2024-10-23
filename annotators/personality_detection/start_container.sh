#!/bin/bash

cd ../../ && docker-compose -f docker-compose.yml -f assistant_dists/dream_ocean/docker-compose.override.yml -f assistant_dists/dream_ocean/dev.yml -p bot_test up --build -d personality-detection
sleep 5
