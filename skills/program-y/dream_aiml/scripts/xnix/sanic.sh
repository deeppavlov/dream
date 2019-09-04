#! /bin/sh

clear

export PYTHONPATH=../../src:$PYTHONPATH

python3 -m templatey.clients.restful.sanic.client --config ../../config/xnix/config.sanic.yaml --cformat yaml --logging ../../config/xnix/logging.yaml
