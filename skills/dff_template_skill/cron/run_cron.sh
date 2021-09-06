#!/usr/bin/env bash
set -e

printenv | sed 's/^\(.*\)\=\(.*\)$/export \1\="\2"/g' > /root/.env

cd "$(dirname "$0")"

bash update_game_db.sh $1

cron
tail -f /var/log/cron.log &

echo "Cron is running"