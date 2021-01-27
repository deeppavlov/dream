#!/usr/bin/env bash

# https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html


for ARGUMENT in "$@"; do

    KEY=$(echo $ARGUMENT | cut -f1 -d=)
    VALUE=$(echo $ARGUMENT | cut -f2 -d=)

    case "$KEY" in
    LAMBDA_NAME) LAMBDA_NAME=${VALUE} ;;
    TARGET) TARGET=${VALUE} ;;
    *) ;;
    esac
done

if [[ "$TARGET" == "dev" ]]; then
    cp .env.staging aws_lambda/.env
    LAMBDA_NAME="dream_staging"
fi
if [[ "$TARGET" == "prod" ]]; then
    cp .env.prod aws_lambda/.env
    LAMBDA_NAME="dp_agent_lambda_proxy_dev"
fi

if [[ "$LAMBDA_NAME" == "" ]]; then
    # also in case if LAMBDA_NAME is custom you should put .env file into aws_lambda folder
    echo "Usage: aws_lambda/deploy.sh TARGET=target or aws_lambda/deploy.sh LAMBDA_NAME=LAMBDA_FUNCTION_NAME"
    exit 1
fi

echo "Deploying lambda_function to $LAMBDA_NAME"


echo "Cleaning old package"
rm -r aws_lambda/package/

if ! pip3 install -r aws_lambda/requirements.txt --target aws_lambda/package &> /dev/null; then
    echo "pip3 was not found, trying pip.."

    if ! pip install -r aws_lambda/requirements.txt --target aws_lambda/package; then
        echo "pip was not found, canceling..."
        exit 1
    fi
fi

cp aws_lambda/main.py aws_lambda/package/
cp aws_lambda/.env aws_lambda/package/
cd aws_lambda/package && zip -r9 dp_agent_lambda.zip . && cd ../..
aws lambda update-function-code --function-name $LAMBDA_NAME --zip-file fileb://aws_lambda/package/dp_agent_lambda.zip
rm aws_lambda/package/dp_agent_lambda.zip
