#!/usr/bin/env bash

for ARGUMENT in "$@"; do

    KEY=$(echo $ARGUMENT | cut -f1 -d=)
    VALUE=$(echo $ARGUMENT | cut -f2 -d=)

    case "$KEY" in
    DEVICE) DEVICE=${VALUE} ;;
    MODE) MODE=${VALUE} ;;
    *) ;;
    esac
done

function wait_service() {
    local timeout=${WAIT_TIMEOUT:-480}
    local interval=${WAIT_INTERVAL:-10}
    local url=$1
    local reply_keyword=$2
    while [[ $timeout -gt 0 ]]; do
        local res=$(curl -s -XGET "$url" | grep "$reply_keyword")
        if [ ! -z "$res" ]; then
            echo FOUND service $url
            echo REPLY: $res
            return 0
        fi
        sleep $interval
        ((timeout-=interval))
        echo wait_service $url timeout in $timeout sec..
    done
    echo ERROR: $url is not responding
    return 1
}

function cleanup() {
    local exit_status=${1:-$?}
    echo SHUTDOWN TESTING ENVIRONMENT..

    dockercompose_cmd stop
    dockercompose_cmd run -T agent bash -c "chown -R $(id -u):$(id -g) /dp-agent"
    dockercompose_cmd run -T agent bash -c "find /dp-agent -name __pycache__ | xargs rm -rf"
    dockercompose_cmd run -T mongo bash -c "rm -rf /root/data/db/*"

    dockercompose_cmd down
    dockercompose_cmd rm mongo
    echo EXIT $0 with STATUS: $exit_status
}

function logger() {
    printf '\e[96m%80s\e[39m\n' | tr ' ' =
    echo -e "\e[44m    \e[49m $@ \e[44m    \e[49m"
    printf '\e[96m%80s\e[39m\n' | tr ' ' =
}

function dockercompose_cmd() {
    # if [[ "$DEVICE" == "cpu" ]]; then
    #     DOCKER_COMPOSE_CMD="docker-compose -f docker-compose.yml -f dev.yml -f cpu.yml -f proxy.yml -f s3.yml -p test"
    # else
        DOCKER_COMPOSE_CMD="docker-compose --no-ansi -p test -f docker-compose.yml -f assistant_dists/nutrition_assistant/docker-compose.override.yml -f assistant_dists/nutrition_assistant/test.yml -f assistant_dists/nutrition_assistant/proxy.yml"
    # fi
    eval '$DOCKER_COMPOSE_CMD "$@"'
    if [[ $? != 0 ]]; then
        logger "FAILED dockercompose_cmd: $@"
    fi
}

function container_is_started() { [ "$(docker ps | grep $1)" ] && return 0 || return 1; }

if [[ "$DEVICE" == "" ]]; then
    DEVICE="gpu"
fi

if [[ "$MODE" == "" ]]; then
    MODE="all"
fi

if [[ "$MODE" == "clean" ]]; then
    cleanup
    exit 0
fi

set -e

#DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR=$(dirname $(realpath -s $0))
#trap cleanup EXIT

echo running tests on $DEVICE in mode: $MODE

echo Loading testing env..
AGENT_PORT=${AGENT_PORT:-4242}

if [[ "$MODE" == "build" ]]; then
  dockercompose_cmd build
  exit 0
fi
#dockercompose_cmd logs -f --tail="all" --timestamps &

if [[ "$MODE" == "start" ]]; then
  dockercompose_cmd up -d
  dockercompose_cmd logs --no-color -f --tail="all" --timestamps &
  wait_service "http://0.0.0.0:$AGENT_PORT/ping" pong
  exit 0
fi

if [[ "$MODE" == "test_skills" || "$MODE" == "all" ]]; then
    # docker-compose -p test -f docker-compose.yml -f dev.yml ps --services | grep -wv -e agent -e mongo

    dockercompose_cmd logs --no-color -f --tail="all" --timestamps &
    echo "Passing test data to each skill selected for testing"


    for container in ranking-based-response-selector prompt-selector dff-nutrition-prompted-skill; do

        echo "Run tests for $container"
        dockercompose_cmd exec -T -u $(id -u) $container ./test.sh
    done

fi
