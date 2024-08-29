#!/bin/bash

docker-compose -f docker-compose.yml -f assistant_dists/dream_emotion/docker-compose.override.yml -f assistant_dists/dream_emotion/dev.yml -f assistant_dists/dream_emotion/proxy.yml -p bot_test up -d bot-emotion-classifier
python annotators/bot_emotion_classifier/test_launch_time.py
python annotators/bot_emotion_classifier/test_time_format.py
docker-compose -f docker-compose.yml -f assistant_dists/dream_emotion/docker-compose.override.yml -f assistant_dists/dream_emotion/dev.yml -f assistant_dists/dream_emotion/proxy.yml -p bot_test down