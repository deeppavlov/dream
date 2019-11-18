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
    local timeout=480
    local url=$1
    local reply_keyword=$2
    while [[ $timeout -gt 0 ]]; do
        local res=$(curl -s -XGET "$url" | grep "$reply_keyword")
        if [ ! -z "$res" ]; then
            echo FOUND service $url
            echo REPLY: $res
            return 0
        fi
        sleep 1
        ((timeout--))
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
    if [[ "$DEVICE" == "cpu" ]]; then
        DOCKER_COMPOSE_CMD="docker-compose -f docker-compose.yml -f dev.yml -f cpu.yml -p test"
    else
        DOCKER_COMPOSE_CMD="docker-compose -f docker-compose.yml -f dev.yml -p test"
    fi
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

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
trap cleanup EXIT

echo running tests on $DEVICE in mode: $MODE

echo Loading testing env..
AGENT_PORT=4242
export AGENT_PORT=$AGENT_PORT

dockercompose_cmd up -d --build
dockercompose_cmd logs -f --tail="all" --timestamps &

wait_service "http://0.0.0.0:$AGENT_PORT/ping" pong

if [[ "$MODE" == "test_dialog" || "$MODE" == "all" ]]; then
    echo "Check workflow bug"
    dockercompose_cmd exec -T -u $(id -u) agent python3 tests/test_workflow_bug.py

    echo "Pass dialogs from dp-agent"
    dockercompose_cmd exec -T -u $(id -u) agent python3 \
        utils/http_api_test.py -u http://0.0.0.0:4242 -cf tests/dream/test_dialogs_gold_phrases.csv -of tests/dream/output/test_dialogs_output.csv

    echo "Assert passed dialogs"
    if [[ "$DEVICE" == "cpu" ]]; then
        dockercompose_cmd exec -T -u $(id -u) agent python3 tests/dream/assert_test_dialogs.py -pred_f tests/dream/output/test_dialogs_output.csv -true_f tests/dream/test_dialogs_gold_phrases.csv -time_limit 20
    else
        dockercompose_cmd exec -T -u $(id -u) agent python3 tests/dream/assert_test_dialogs.py -pred_f tests/dream/output/test_dialogs_output.csv -true_f tests/dream/test_dialogs_gold_phrases.csv
    fi
fi

if [[ "$MODE" == "test_skills" || "$MODE" == "all" ]]; then
    echo "Passing test data to each skill selected for testing"

    if container_is_started sentiment_classification; then
        echo "Passing test data to sentiment_classification"
        dockercompose_cmd exec -T -u $(id -u) sentiment_classification python annotators/DeepPavlovSentimentClassification/tests/run_test.py
    fi

    if container_is_started transfertransfo; then
        echo "Passing test data to transfertransfo"
        dockercompose_cmd exec -T -u $(id -u) transfertransfo python tests/run_test.py \
            --true_file tests/test_tasks.json \
            --pred_file tests/test_results.json \
            --from_url http://0.0.0.0:8007/transfertransfo

        # echo "Passing question test data to transfertransfo from dream/...xlsx , it takes about 3 hours"
        # dockercompose_cmd exec -T -u $(id -u) transfertransfo python tests/run_test.py \
        #     --true_file tests/test_question_tasks.json \
        #     --pred_file tests/test_question_tasks_results.json \
        #     --from_url http://0.0.0.0:8007/transfertransfo
    fi

    if container_is_started movie_skill; then
        echo "Run tests for movie_skill"
        dockercompose_cmd exec -T -u $(id -u) movie_skill python test.py
    fi

fi

if [[ "$MODE" == "infer_questions" || "$MODE" == "all" ]]; then
    echo "Passing questions to Alexa"
    dockercompose_cmd exec -T -u $(id -u) agent python3 \
        utils/xlsx_responder.py --url http://0.0.0.0:4242 \
        --input 'tests/dream/test_questions.xlsx' \
        --output 'tests/dream/output/test_questions_output.xlsx'

    echo "Computing Q&A metrics"
    dockercompose_cmd exec -T -u $(id -u) agent python3 \
        tests/dream/compute_qa_metrics.py \
        --pred_file 'tests/dream/output/test_questions_output.xlsx' \
        --output 'tests/dream/output/qa_metrics.txt'
fi
