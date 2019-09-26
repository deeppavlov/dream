#!/usr/bin/env bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
trap cleanup EXIT

function wait_service()
{
    local timeout=480
    local url=$1
    local reply_keyword=$2
    while [[ $timeout -gt 0 ]]; do
        local res=$(curl -s -XGET "$url" | grep "$reply_keyword")
        if [ ! -z "$res" ]
        then
            echo FOUND service $url
            echo REPLY: $res
            return 0
        fi
        sleep 1
        (( timeout-- ))
        echo wait_service $url timeout in $timeout sec..
    done
    echo ERROR: $url is not responding
    return 1
}

function cleanup()
{
    local exit_status=${1:-$?}
    echo SHUTDOWN TESTING ENVIRONMENT..

    dockercompose_cmd down
    echo EXIT $0 with STATUS: $exit_status
}

function logger() {
    printf '\e[96m%80s\e[39m\n' | tr ' ' =
    echo -e "\e[44m    \e[49m $@ \e[44m    \e[49m"
    printf '\e[96m%80s\e[39m\n' | tr ' ' =
}

function dockercompose_cmd() {
    DOCKER_COMPOSE_CMD="docker-compose -f docker-compose.yml -f dev.yml -p test"
    eval '$DOCKER_COMPOSE_CMD "$@"'
    if [[ $? != 0 ]]; then
        logger "FAILED dockercompose_cmd: $@"
    fi
}


echo Loading testing env..
AGENT_PORT=4242
export AGENT_PORT=$AGENT_PORT

dockercompose_cmd up -d
dockercompose_cmd logs -f --tail="all" --timestamps &

wait_service "http://0.0.0.0:$AGENT_PORT/ping" pong

echo "Pass dialogs from dp-agent"
dockercompose_cmd exec agent python3 \
  utils/http_api_test.py -u http://0.0.0.0:4242 -df tests/dream/test_dialogs.json -of tests/dream/test_dialogs_output.csv

echo "Assert passed dialogs"
dockercompose_cmd exec agent python3 tests/dream/assert_test_dialogs.py -pred_f tests/dream/test_dialogs_output.csv -true_f tests/dream/test_dialogs_gold_phrases.csv
