#!/usr/bin/env bash

printenv | sed 's/^\(.*\)\=\(.*\)$/export \1\="\2"/g' > /cron_env/.env
cron