#!/usr/bin/env bash

set -e

STAGING_DP_AGENT_URL=`cat .env.staging | grep -oP "DP_AGENT_URL=\K.*"`
PROD_DP_AGENT_URL=`cat .env.prod | grep -oP "DP_AGENT_URL=\K.*"`

echo "Deploying PROD version to staging cluster..."
./deploy.sh MODE=all TARGET=dev
# sleep to make sure that old agent is stopped
sleep 30;
while [[ "$(curl -m 5 -s -o /dev/null -w ''%{http_code}'' $STAGING_DP_AGENT_URL/ping)" != "200" ]]; do
  echo "waiting till agent is up on staging...";
  sleep 5;
done
# to finish services loading
sleep 60;

# warmup query to staging
curl --header "Content-Type: application/json" --data '{"user_id":"deploy","payload":"/start"}' --request POST -m 5 -s -o /dev/null -w ''%{http_code}'' $STAGING_DP_AGENT_URL
while [[ "$(curl --header "Content-Type: application/json" --data '{"user_id":"deploy","payload":"after_deploy_warm"}' --request POST -m 5 -s -o /dev/null -w ''%{http_code}'' $STAGING_DP_AGENT_URL)" != "200" ]]; do
  echo "waiting till STAGING agent responded to QUERY with 200 status code";
  sleep 5;
done

echo "Deploying PROD version to staging cluster... done"

echo "Changing PROD lambda url to staging..."
sed -i 's/DP_AGENT_URL=.*/'"$(printf '%s\n' "$(cat .env.staging | grep DP_AGENT_URL)" | sed 's:[][\/.^$*]:\\&:g')"'/g' .env.prod
./deploy.sh MODE=lambda TARGET=prod
echo "Changing PROD lambda url to staging... done"

echo "Deploying agent to PROD cluster..."
./deploy.sh MODE=agent TARGET=prod
sleep 30;
while [[ "$(curl -m 5 -s -o /dev/null -w ''%{http_code}'' $PROD_DP_AGENT_URL/ping)" != "200" ]]; do
  echo "waiting till agent is up on prod...";
  sleep 5;
done
sleep 60;

# warmup query to prod
curl --header "Content-Type: application/json" --data '{"user_id":"deploy","payload":"/start"}' --request POST -m 5 -s -o /dev/null -w ''%{http_code}'' $PROD_DP_AGENT_URL
while [[ "$(curl --header "Content-Type: application/json" --data '{"user_id":"deploy","payload":"after_deploy_warm"}' --request POST -m 5 -s -o /dev/null -w ''%{http_code}'' $PROD_DP_AGENT_URL)" != "200" ]]; do
  echo "waiting till PROD agent responded to QUERY with 200 status code";
  sleep 5;
done

echo "Deploying agent to PROD cluster... done"

echo "Changing PROD lambda url to prod..."
git checkout .env.prod
./deploy.sh MODE=lambda TARGET=prod
echo "Changing PROD lambda url to prod... done"

# echo "Deploying dev to staging"
# git checkout dev # how to make run it on Jenkins?
# ./deploy.sh MODE=all TARGET=dev

echo "PROD is successfully deployed"
exit 0
