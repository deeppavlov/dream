#!/bin/bash

mkdir -p /root/.deeppavlov

echo "wget ${DATA_URL}"
wget -nc -q ${DATA_URL} -P /root/.deeppavlov
echo "wget finished"

gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --reload --timeout 800
