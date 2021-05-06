#!/bin/bash

mkdir -p /root/.deeppavlov

wget -ncq ${DATA_URL} -P /root/.deeppavlov

gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --reload --timeout 800
