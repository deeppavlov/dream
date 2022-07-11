#!/bin/bash

python3 services/image_captioning_large/ping.py
python3 -m pytest services/image_captioning_large
docker stop dream-image-captioning-large-1