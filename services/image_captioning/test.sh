#!/bin/bash

python3 services/image_captioning/ping.py
python3 -m pytest services/image_captioning
docker stop dream_image-captioning_1