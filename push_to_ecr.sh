#!/usr/bin/env bash

#set -e

# https://stackoverflow.com/a/51663052

export VERSION=$VERSION
export ENV_FILE=$ENV_FILE
export DP_AGENT_PORT=$DP_AGENT_PORT
eval $(aws ecr get-login --no-include-email)

for r in $(grep 'image: \${DOCKER_REGISTRY}' staging.yml | sed -e 's|^.*/||' | sed -e 's|:.*||')
 do
  # TODO: сейчас если репа уже есть, то тут ошибка появляется, надо ее не показывать
  echo "$r"
  aws ecr create-repository --repository-name "$r"
 done

docker-compose -f docker-compose.yml -f staging.yml -f s3.yml build

RET=1
MAX_N_TRIES=15
N_TRY=1
until [ "$N_TRY" -gt "$MAX_N_TRIES" ] || [ "$RET" -eq 0 ]; do
    echo "Trying to push to ECR, try number: $N_TRY"
    docker-compose -f docker-compose.yml -f staging.yml -f s3.yml push
    RET=$?
    N_TRY=$((N_TRY + 1))
    sleep 5
done

exit $RET