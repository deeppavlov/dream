#! /bin/sh

clear

export PYTHONPATH=../../src:$PYTHONPATH

python3 -m programy.clients.events.console.client --config ../../config/xnix/config.yaml --cformat yaml --logging ../../config/xnix/logging.yaml
