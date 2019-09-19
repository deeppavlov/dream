#!/usr/bin/env bash

#set -e

# https://stackoverflow.com/a/51663052

eval $(aws ecr get-login --no-include-email)

for r in $(grep 'image: \${DOCKER_REGISTRY}' staging.yml | sed -e 's/^.*\///')
 do
  # TODO: сейчас если репа уже есть, то тут ошибка появляется, надо ее не показывать
  echo "$r"
  aws ecr create-repository --repository-name "$r"
 done

docker-compose -f docker-compose.yml -f staging.yml build
docker-compose -f docker-compose.yml -f staging.yml push
