#!/usr/bin/env bash

set -e

# ssh keys should be added to ssh-agent!
# eval "$(ssh-agent -s)"
# ssh-add ...

echo "Warning! You are going to deploy A/B tests:"
echo "1. Check that A and B versions .env.prod files do not containt A/B tests configuration!"
echo "2. If currently no A/B tests are running run 'docker stack rm dream_prod' to delete prod stack"
echo "3. If you want to deploy new version without A/B tests don't forget to remove A/B tests stacks!"

read -p "Continue (y/n)?" choice
case "$choice" in 
  y|Y ) echo "ok, go!";;
  n|N ) exit 0;;
  * ) exit 0;;
esac

A_VERSION=`cat .env.prod | grep -oP "A_VERSION=\K.*"`
A_AGENT_URL=`cat .env.prod | grep -oP "A_AGENT_URL=\K.*"`
A_AGENT_PORT=`cat .env.prod | grep -oP "A_AGENT_PORT=\K.*"`
B_VERSION=`cat .env.prod | grep -oP "B_VERSION=\K.*"`
B_AGENT_URL=`cat .env.prod | grep -oP "B_AGENT_URL=\K.*"`
B_AGENT_PORT=`cat .env.prod | grep -oP "B_AGENT_PORT=\K.*"`

echo "A_VERSION"=$A_VERSION
echo "B_VERSION"=$B_VERSION

echo "Preparing repo for $A_VERSION"
rm -rf ../dp-agent-alexa-A
mkdir ../dp-agent-alexa-A
cd ../dp-agent-alexa-A
git clone git@github.com:sld/dp-agent-alexa.git .
git fetch --tags
git checkout $A_VERSION

echo "Preparing repo for $B_VERSION"
rm -rf ../dp-agent-alexa-B
mkdir ../dp-agent-alexa-B
cd ../dp-agent-alexa-B
git clone git@github.com:sld/dp-agent-alexa.git .
git fetch --tags
git checkout $B_VERSION


cd ../dp-agent-alexa-A
echo "Deploying A $A_VERSION version to staging cluster..."
./deploy.sh MODE=all TARGET=dev
echo "Deploying A $A_VERSION version to staging cluster... done"

echo "Changing PROD lambda url to staging..."
# assuming that staging agent port is 4242 and prod agent port is also 4242 (as default), we change only URL
sed -i 's/DP_AGENT_URL=.*/'"$(printf '%s\n' "$(cat .env.staging | grep DP_AGENT_URL)" | sed 's:[][\/.^$*]:\\&:g')"'/g' .env.prod
./deploy.sh MODE=lambda TARGET=prod
git checkout .env.prod
echo "Changing PROD lambda url to staging... done"

echo "set A/B DP_AGENT_URLs in .env.prod files and updating deploy scripts, compose files"
# remove DP_AGENT_URL and DP_AGENT_PORT lines from .env.prod file
sed -i '/DP_AGENT_URL/d' ../dp-agent-alexa-A/.env.prod
sed -i '/DP_AGENT_PORT/d' ../dp-agent-alexa-A/.env.prod
sed -i '/DP_AGENT_URL/d' ../dp-agent-alexa-B/.env.prod
sed -i '/DP_AGENT_PORT/d' ../dp-agent-alexa-B/.env.prod

# add *_AGENT_URL line with DP_AGENT_URL from .end.prod with A/B settings
cat ../dp-agent-alexa/.env.prod | grep A_AGENT_URL >> ../dp-agent-alexa-A/.env.prod
cat ../dp-agent-alexa/.env.prod | grep A_AGENT_PORT >> ../dp-agent-alexa-A/.env.prod
sed -i 's/A_AGENT_URL/DP_AGENT_URL/' ../dp-agent-alexa-A/.env.prod
sed -i 's/A_AGENT_PORT/DP_AGENT_PORT/' ../dp-agent-alexa-A/.env.prod

cat ../dp-agent-alexa/.env.prod | grep B_AGENT_URL >> ../dp-agent-alexa-B/.env.prod
cat ../dp-agent-alexa/.env.prod | grep B_AGENT_PORT >> ../dp-agent-alexa-B/.env.prod
sed -i 's/B_AGENT_URL/DP_AGENT_URL/' ../dp-agent-alexa-B/.env.prod
sed -i 's/B_AGENT_PORT/DP_AGENT_PORT/' ../dp-agent-alexa-B/.env.prod

cp ../dp-agent-alexa/deploy.sh ../dp-agent-alexa-A/
cp ../dp-agent-alexa/deploy.sh ../dp-agent-alexa-B/
cp ../dp-agent-alexa/push_to_ecr.sh ../dp-agent-alexa-A/
cp ../dp-agent-alexa/push_to_ecr.sh ../dp-agent-alexa-B/
cp -n ../dp-agent-alexa/s3.yml ../dp-agent-alexa-A/ || true
cp -n ../dp-agent-alexa/s3.yml ../dp-agent-alexa-B/ || true
python3 ../dp-agent-alexa/utils/clean_ports_docker_compose.py --dc ../dp-agent-alexa-A/docker-compose.yml --staging ../dp-agent-alexa-A/staging.yml
python3 ../dp-agent-alexa/utils/clean_ports_docker_compose.py --dc ../dp-agent-alexa-B/docker-compose.yml --staging ../dp-agent-alexa-B/staging.yml

echo "Deploying agent A $A_VERSION to PROD cluster..."
cd ../dp-agent-alexa-A
./deploy.sh MODE=agent TARGET=prod STACK=A
echo "Deploying agent A to PROD cluster... done"

echo "Deploying agent B $B_VERSION to PROD cluster..."
cd ../dp-agent-alexa-B
./deploy.sh MODE=agent TARGET=prod STACK=B
echo "Deploying agent B to PROD cluster... done"

echo "Changing PROD lambda to A/B urls..."
cd ../dp-agent-alexa/
# .env.prod must have A and B URLs
./deploy.sh MODE=lambda TARGET=prod
echo "Changing PROD lambda url to A/B urls... done"


echo "A/B tests are successfully deployed"
exit 0