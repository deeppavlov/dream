#!/bin/bash

cd "$(dirname "$0")"

source /root/.env

python update_game_db.py