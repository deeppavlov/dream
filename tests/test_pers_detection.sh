#!/bin/bash

docker-compose -f docker-compose.yml -f assistant_dists/dream_ocean/docker-compose.override.yml -f assistant_dists/dream_ocean/dev.yml -p bot_test up -d personality-detection
python annotators/personality_detection/test_launch_time.py
python annotators/personality_detection/test_time_format.py
python annotators/personality_detection/test_accuracy.py
docker-compose -f docker-compose.yml -f assistant_dists/dream_ocean/docker-compose.override.yml -f assistant_dists/dream_ocean/dev.yml -p bot_test down