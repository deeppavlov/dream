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
        DOCKER_COMPOSE_CMD="docker-compose -f docker-compose.yml -f dev.yml -f jenkins_cpu.yml -p test"
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
    echo "Warmup for tests"
    dockercompose_cmd exec -T -u $(id -u) agent python3 tests/dream/test_response.py

    echo "Test workflow bug and asr"
    dockercompose_cmd exec -T -u $(id -u) agent python3 tests/test_workflow_bug_and_asr.py

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

    if container_is_started movie_skill; then
        echo "Run tests for movie_skill"
        dockercompose_cmd exec -T -u $(id -u) movie_skill python test.py
    fi

    if container_is_started asr; then
        echo "Run tests for asr container"
        dockercompose_cmd exec -T -u $(id -u) asr python test.py
    fi

    if container_is_started weather_skill; then
        echo "Run tests for weather_skill container"
        dockercompose_cmd exec -T -u $(id -u) weather_skill python test_weather_skill_policy.py
    fi

    if container_is_started program_y; then
        echo "Run tests for program_y container"
        dockercompose_cmd exec -T -u $(id -u) program_y python /src/test.py

        echo "Run lets_chat tests for program_y container"
        dockercompose_cmd exec -T -u $(id -u) program_y python /src/test_lets_chat.py
    fi

    if container_is_started program_y_dangerous; then
        echo "Run tests for program_y_dangerous container"
        dockercompose_cmd exec -T -u $(id -u) program_y_dangerous python /src/test.py
    fi

    if container_is_started superbowl_skill; then
        echo "Run tests for superbowl_skill container"
        dockercompose_cmd exec -T -u $(id -u) superbowl_skill python /src/test_server.py
    fi

    if container_is_started oscar_skill; then
        echo "Run tests for oscar_skill container"
        dockercompose_cmd exec -T -u $(id -u) oscar_skill python /src/test_server.py
    fi

    if container_is_started topicalchat_convert_retrieval; then
        echo "Run tests for topicalchat_convert_retrieval container"
        dockercompose_cmd exec -T -u $(id -u) topicalchat_convert_retrieval python /src/test_server.py
    fi

    if container_is_started valentines_day_skill; then
        echo "Run tests for valentines_day_skill container"
        dockercompose_cmd exec -T -u $(id -u) valentines_day_skill python /src/test_server.py
    fi

    if container_is_started eliza; then
        echo "Run tests for eliza container"
        dockercompose_cmd exec -T -u $(id -u) eliza python /src/test_server.py
    fi

    if container_is_started news_skill; then
        echo "Run tests for news_skill"
        dockercompose_cmd exec -T -u $(id -u) news_skill python /src/src/test.py
    fi

    if container_is_started dummy_skill_dialog; then
        echo "Run tests for dummy_skill_dialog"
        dockercompose_cmd exec -T -u $(id -u) dummy_skill_dialog python test.py
    fi

    if container_is_started intent_catcher; then
        echo "Run tests for intent_catcher"
        dockercompose_cmd exec -T -u $(id -u) intent_catcher python test.py
    fi

    if container_is_started comet_atomic; then
        echo "Run tests for comet_atomic"
        dockercompose_cmd exec -T -u $(id -u) comet_atomic python /comet/test_atomic.py
    fi

    if container_is_started comet_conceptnet; then
        echo "Run tests for comet_conceptnet"
        dockercompose_cmd exec -T -u $(id -u) comet_conceptnet python /comet/test_conceptnet.py
    fi

    if container_is_started reddit_ner_skill; then
        echo "Run tests for reddit_ner_skill"
        dockercompose_cmd exec -T -u $(id -u) reddit_ner_skill python test.py
    fi

    if container_is_started convers_evaluation_selector; then
        echo "Run tests for convers_evaluation_selector"
        dockercompose_cmd exec -T -u $(id -u) convers_evaluation_selector python test.py
    fi
    if container_is_started book_skill; then
        echo "Run tests for book_skill"
        dockercompose_cmd exec -T -u $(id -u) book_skill python test.py
    fi
    if container_is_started emotion_skill; then
        echo "Run tests for emotion_skill"
        dockercompose_cmd exec -T -u $(id -u) emotion_skill python test.py
    fi
fi

if [[ "$MODE" == "infer_questions" || "$MODE" == "all" ]]; then
    echo "Passing questions to Alexa"
    dockercompose_cmd exec -T -u $(id -u) agent python3 tests/dream/test_response.py
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
