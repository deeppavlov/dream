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
        DOCKER_COMPOSE_CMD="docker-compose --no-ansi -p dream -f docker-compose.yml -f assistant_dists/dream_multilingual/docker-compose.override.yml -f assistant_dists/dream_multilingual/test.yml"
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

if [[ "$MODE" == "test_dialog" || "$MODE" == "all" ]]; then
    GOLD_OUTPUT_FILE="GOLD-"$(date '+%Y-%m-%d_%H-%M-%S')".csv"
    dockercompose_cmd logs --no-color -f --tail="all" --timestamps &
    echo "Warmup for tests"
    dockercompose_cmd exec -T -u $(id -u) agent python3 tests/dream_multilingual/test_response.py

    echo "Test workflow bug and asr"
    dockercompose_cmd exec -T -u $(id -u) agent python3 tests/test_workflow_bug_and_asr.py

    echo "Pass dialogs from dp-agent"
    dockercompose_cmd exec -T -u $(id -u) agent python3 \
        utils/http_api_test.py -u http://0.0.0.0:4242 -cf tests/dream_multilingual/test_dialogs_gold_phrases.csv -of tests/dream_multilingual/output/$GOLD_OUTPUT_FILE

    echo "Assert passed dialogs"
    if [[ "$DEVICE" == "cpu" ]]; then
        dockercompose_cmd exec -T -u $(id -u) agent python3 tests/dream_multilingual/assert_test_dialogs.py -pred_f tests/dream_multilingual/output/$GOLD_OUTPUT_FILE -true_f tests/dream_multilingual/test_dialogs_gold_phrases.csv -time_limit 20
    else
        dockercompose_cmd exec -T -u $(id -u) agent python3 tests/dream_multilingual/assert_test_dialogs.py -pred_f tests/dream_multilingual/output/$GOLD_OUTPUT_FILE -true_f tests/dream_multilingual/test_dialogs_gold_phrases.csv -time_limit 10
    fi

    echo "Testing file conflicts"
    dockercompose_cmd exec -T agent sh -c 'cd /pavlov/DeepPavlov && git fetch --all --tags --prune && git checkout 0.14.1 && cd /dp-agent/ && python utils/analyze_downloads.py --compose_file assistant_dists/dream_multilingual/docker-compose.override.yml'

    echo "Testing docker-compose files"
    dockercompose_cmd exec -T -u $(id -u) agent python utils/verify_compose.py -d assistant_dists/dream_multilingual
fi

if [[ "$MODE" == "test_skills" || "$MODE" == "all" ]]; then
    # docker-compose -f docker-compose.yml -f dev.yml ps --services | grep -wv -e agent -e mongo

    dockercompose_cmd logs --no-color -f --tail="all" --timestamps &
    echo "Passing test data to each skill selected for testing"


    for container in convers-evaluation-selector gpt2-multilingual toxic-classification-multilingual
                     sentiment-classification-multilingual \
                     sentence-ranker-multilingual; do

        echo "Run tests for $container"
        dockercompose_cmd exec -T -u $(id -u) $container ./test.sh
    done

fi

if [[ "$MODE" == "infer_questions" || "$MODE" == "all" ]]; then
    dockercompose_cmd logs --no-color -f --tail="all" --timestamps &
    echo "Passing questions to Alexa"
    dockercompose_cmd exec -T -u $(id -u) agent python3 tests/dream_multilingual/test_response.py
    dockercompose_cmd exec -T -u $(id -u) agent python3 \
        utils/xlsx_responder.py --url http://0.0.0.0:4242 \
        --input 'tests/dream_multilingual/test_questions.xlsx' \
        --output 'tests/dream_multilingual/output/test_questions_output.xlsx'

    echo "Computing Q&A metrics"
    dockercompose_cmd exec -T -u $(id -u) agent python3 \
        tests/dream_multilingual/compute_qa_metrics.py \
        --pred_file 'tests/dream_multilingual/output/test_questions_output.xlsx' \
        --output 'tests/dream_multilingual/output/qa_metrics.txt'
fi
