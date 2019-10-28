#!/usr/bin/env bash

for ARGUMENT in "$@"; do

    KEY=$(echo $ARGUMENT | cut -f1 -d=)
    VALUE=$(echo $ARGUMENT | cut -f2 -d=)

    case "$KEY" in
    TARGET) TARGET=${VALUE} ;;
    MODE) MODE=${VALUE} ;;
    *) ;;
    esac
done

set -e

if [[ "$MODE" == "lambda" || "$MODE" == "all" ]]; then
  echo "Deploying lambda"
  ./aws_lambda/deploy.sh TARGET=$TARGET
fi

if [[ "$TARGET" == "prod" ]]; then
  ENV_FILE=".env.prod"
  DOCKER_HOST="localhost:2374"
  REGISTRY_AUTH="dream_prod"
elif [[ "$TARGET" == "dev" ]]; then
  ENV_FILE=".env.staging"
  DOCKER_HOST="localhost:2375"
  REGISTRY_AUTH="dream_staging"
else
  echo "Unknown TARGET: $TARGET"
  exit 1
fi

if [[ "$MODE" == "agent" || "$MODE" == "all" ]]; then
  echo "Deploying agent"
  printf "\t Pushing to ECR\n"
  VERSION="$(git rev-parse --short HEAD)" ENV_FILE=$ENV_FILE DOCKER_REGISTRY=807746935730.dkr.ecr.us-east-1.amazonaws.com ./push_to_ecr.sh
  printf "\t Docker stack deploy\n"
  VERSION="$(git rev-parse --short HEAD)" ENV_FILE=$ENV_FILE DOCKER_REGISTRY=807746935730.dkr.ecr.us-east-1.amazonaws.com DOCKER_HOST=$DOCKER_HOST docker stack deploy --compose-file docker-compose.yml,staging.yml --with-registry-auth $REGISTRY_AUTH
fi

echo "Successfully deployed"
exit 0