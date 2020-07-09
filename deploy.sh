#!/usr/bin/env bash

for ARGUMENT in "$@"; do

    KEY=$(echo $ARGUMENT | cut -f1 -d=)
    VALUE=$(echo $ARGUMENT | cut -f2 -d=)

    case "$KEY" in
    TARGET) TARGET=${VALUE} ;;
    MODE) MODE=${VALUE} ;;
    STACK) STACK=${VALUE} ;;
    *) ;;
    esac
done

set -e

if [[ "$TARGET" == "prod" ]]; then
  ENV_FILE=".env.prod"
  DOCKER_HOST="localhost:2374"
  REGISTRY_AUTH="dream_prod"
  TELEGRAM_AGENT=""
  DP_AGENT_URL=`cat .env.prod | grep -oP "DP_AGENT_URL=\K.*"`
  DP_AGENT_PORT=`cat .env.prod | grep -oP "DP_AGENT_PORT=\K.*"`
elif [[ "$TARGET" == "dev" ]]; then
  ENV_FILE=".env.staging"
  DOCKER_HOST="localhost:2375"
  REGISTRY_AUTH="dream_staging"
  TELEGRAM_AGENT=",telegram_agent.yml"
  DP_AGENT_URL=`cat .env.staging | grep -oP "DP_AGENT_URL=\K.*"`
  DP_AGENT_PORT=`cat .env.staging | grep -oP "DP_AGENT_PORT=\K.*"`
else
  echo "Unknown TARGET: $TARGET"
  exit 1
fi

if [[ "$STACK" != "" ]]; then
  REGISTRY_AUTH="$REGISTRY_AUTH"_"$STACK"
fi

if [[ "$MODE" == "agent" || "$MODE" == "all" ]]; then
  echo "Deploying agent"
  printf "\t Pushing to ECR\n"
  VERSION="$(git rev-parse --short HEAD)" ENV_FILE=$ENV_FILE DP_AGENT_PORT=$DP_AGENT_PORT DOCKER_REGISTRY=807746935730.dkr.ecr.us-east-1.amazonaws.com ./push_to_ecr.sh
  printf "\t Docker stack rm\n"
  DOCKER_HOST=$DOCKER_HOST docker stack rm $REGISTRY_AUTH

  printf "\t Waiting till all down and network removed..\n"
  limit=15
  until [ -z "$(DOCKER_HOST=$DOCKER_HOST docker service ls --filter label=com.docker.stack.namespace=$REGISTRY_AUTH -q)" ] || [ "$limit" -lt 0 ]; do
    sleep 2
    limit="$((limit-1))"
  done

  limit=15;
  until [ -z "$(DOCKER_HOST=$DOCKER_HOST docker network ls --filter label=com.docker.stack.namespace=$REGISTRY_AUTH -q)" ] || [ "$limit" -lt 0 ]; do
    sleep 2;
    limit="$((limit-1))";
  done

  printf "\t Removing stopped containers.."
  DOCKER_HOST=$DOCKER_HOST docker service update --force docker-rm
  sleep 10;

  printf "\t Docker stack deploy\n"
  VERSION="$(git rev-parse --short HEAD)" ENV_FILE=$ENV_FILE DOCKER_REGISTRY=807746935730.dkr.ecr.us-east-1.amazonaws.com DOCKER_HOST=$DOCKER_HOST DP_AGENT_PORT=$DP_AGENT_PORT docker stack deploy --prune --compose-file docker-compose.yml,staging.yml$TELEGRAM_AGENT --with-registry-auth $REGISTRY_AUTH

  echo "$TARGET: waiting till services loaded for 90 seconds"
  sleep 90;

  echo "$TARGET: waiting till agent is up on $DP_AGENT_URL:$DP_AGENT_PORT ...";
  while [[ "$(curl -m 5 -s -o /dev/null -w ''%{http_code}'' $DP_AGENT_URL:$DP_AGENT_PORT/ping)" != "200" ]]; do
    echo "$TARGET: waiting till agent is up...";
    sleep 5;
  done
  echo "$TARGET: /ping works";

  echo "$TARGET: waiting till agent responded to /start on $DP_AGENT_URL:$DP_AGENT_PORT";
  while [[ "$(curl --header "Content-Type: application/json" --data '{"user_id":"deploy","payload":"/start", "ignore_deadline_timestamp": "true"}' --request POST -m 5 -s -o /dev/null -w ''%{http_code}'' $DP_AGENT_URL:$DP_AGENT_PORT)" != "200" ]]; do
    echo "$TARGET: waiting till agent responded to /start with 200 status code";
    sleep 5;
  done
  echo "$TARGET: success response to /start";

  echo "$TARGET: waiting till agent responded to QUERY on $DP_AGENT_URL:$DP_AGENT_PORT";
  while [[ "$(curl --header "Content-Type: application/json" --data '{"user_id":"deploy","payload":"after_deploy_warm", "ignore_deadline_timestamp": "true"}' --request POST -m 5 -s -o /dev/null -w ''%{http_code}'' $DP_AGENT_URL:$DP_AGENT_PORT)" != "200" ]]; do
    echo "$TARGET: waiting till agent responded to QUERY with 200 status code";
    curl --header "Content-Type: application/json" --data '{"user_id":"deploy","payload":"/start", "ignore_deadline_timestamp": "true"}' --request POST -m 5 -s -o /dev/null $DP_AGENT_URL:$DP_AGENT_PORT
    sleep 5;
  done
  echo "$TARGET success agent response to QUERY";
fi

echo "Successfully deployed"
exit 0
