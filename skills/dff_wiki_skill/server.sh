#!/bin/bash

mkdir -p /data

wget -nc ${DATA_URL} -P /data

gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --reload --timeout 800
