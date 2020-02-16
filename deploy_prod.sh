#!/usr/bin/env bash

set -e

STAGING_DP_AGENT_URL=`cat .env.staging | grep -oP "DP_AGENT_URL=\K.*"`
PROD_DP_AGENT_URL=`cat .env.prod | grep -oP "DP_AGENT_URL=\K.*"`

echo "Deploying PROD version to staging cluster..."
./deploy.sh MODE=all TARGET=dev
echo "Deploying PROD version to staging cluster... done"

echo "Changing PROD lambda url to staging..."
sed -i 's/DP_AGENT_URL=.*/'"$(printf '%s\n' "$(cat .env.staging | grep DP_AGENT_URL)" | sed 's:[][\/.^$*]:\\&:g')"'/g' .env.prod
./deploy.sh MODE=lambda TARGET=prod
echo "Changing PROD lambda url to staging... done"

echo "Deploying agent to PROD cluster..."
./deploy.sh MODE=agent TARGET=prod
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
