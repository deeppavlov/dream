#!/bin/bash

docker-compose -f docker-compose.yml -f assistant_dists/dream_kg/docker-compose.override.yml -f assistant_dists/dream_kg/dev.yml -p bot_test up -d property-extraction
python annotators/property_extraction/launch_time_test.py
python annotators/property_extraction/bleu_score_test.py
python annotators/property_extraction/test_property_extraction.py
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg/docker-compose.override.yml -f assistant_dists/dream_kg/dev.yml -p bot_test down