#!/bin/bash

docker-compose -f docker-compose.yml -f assistant_dists/dream_emotion/docker-compose.override.yml -f assistant_dists/dream_emotion/dev.yml -f assistant_dists/dream_emotion/proxy.yml -p bot_test up -d openai-api-chatgpt
docker-compose -f docker-compose.yml -f assistant_dists/dream_emotion/docker-compose.override.yml -f assistant_dists/dream_emotion/dev.yml -f assistant_dists/dream_emotion/proxy.yml -p bot_test up -d emotional-bot-response
python annotators/emotional_bot_response/test_launch_time.py
python annotators/emotional_bot_response/test_time_format.py
docker-compose -f docker-compose.yml -f assistant_dists/dream_emotion/docker-compose.override.yml -f assistant_dists/dream_emotion/dev.yml -f assistant_dists/dream_emotion/proxy.yml -p bot_test down