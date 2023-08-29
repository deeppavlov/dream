#!/usr/bin/env bash

. /home/ubuntu/venv/bin/activate

for ARGUMENT in "$@"; do

    KEY=$(echo $ARGUMENT | cut -f1 -d=)
    VALUE=$(echo $ARGUMENT | cut -f2 -d=)

    case "$KEY" in
    DEVICE) DEVICE=${VALUE} ;;
    MODE) MODE=${VALUE} ;;
    BOT) BOT=${VALUE} ;;
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

FILES="-f docker-compose.yml -f assistant_dists/$BOT/docker-compose.override.yml -f assistant_dists/$BOT/dev.yml -f dp/proxy.yml"

function dockercompose_cmd() {
    DOCKER_COMPOSE_CMD="docker compose --no-ansi -p test $FILES"
    eval '$DOCKER_COMPOSE_CMD "$@"'
    exit $?
}

function add_google_keys() {
    echo 'GOOGLE_API_KEY=$GOOGLE_API_KEY' >> .env
    echo 'GOOGLE_CSE_ID=$GOOGLE_CSE_ID' >> .env
}

function add_openai_key() {
    echo 'OPENAI_API_KEY=$OPENAI_API_KEY' >> .env
}

if [[ "$MODE" == "add-google" ]]; then
    add_google_keys
fi

if [[ "$MODE" == "add-openai" ]]; then
    add_openai_key
fi

if [[ "$MODE" == "build" ]]; then
  dockercompose_cmd build
fi

function cleanup() {
    local exit_status=${1:-$?}
    echo SHUTDOWN TESTING ENVIRONMENT..

    docker run --rm -v $(pwd):/tmp -e UID=$(id -u) ubuntu:mantic chown -R $UID /tmp
    python tests/Docker/test.py $FILES --mode clean
    docker run --rm -v $(pwd):/tmp -e UID=$(id -u) ubuntu:mantic chown -R $UID /tmp

    dockercompose_cmd down
    dockercompose_cmd rm mongo
    python tests/Docker/test.py $FILES --mode clean
    echo EXIT $0 with STATUS: $exit_status
}

if [[ "$MODE" == "start" ]]; then
  python tests/Docker/test.py $FILES --mode up
fi

if [[ "$MODE" == "clean" ]]; then
    cleanup
    exit 0
fi

if [[ "$MODE" == "test" ]]; then
    dockercompose_cmd exec -T -u $(id -u) -e OPENAI_API_KEY=$OPENAI_API_KEY agent python3 tests/test.py $BOT
    exit 0
fi

if [[ "$MODE" == "logs" ]]; then
    python tests/Docker/test.py $FILES --mode logs
fi
