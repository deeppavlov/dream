#!/usr/bin/env bash

# https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html

LAMBDA_NAME=$1
if [ "$LAMBDA_NAME" = "" ]; then
	echo "Usage: aws_lambda/deploy.sh LAMBDA_FUNCTION_NAME"
	exit 1
fi

if ! pip3 install -r aws_lambda/requirements.txt --target aws_lambda/package &> /dev/null; then
    echo "pip3 was not found, trying pip.."

    if ! pip install -r aws_lambda/requirements.txt --target aws_lambda/package; then
        echo "pip was not found, canceling..."
        exit 1
    fi
fi

cp aws_lambda/main.py aws_lambda/package/
cd aws_lambda/package && zip -r9 dp_agent_lambda.zip . && cd ../..
aws lambda update-function-code --function-name $LAMBDA_NAME --zip-file fileb://aws_lambda/package/dp_agent_lambda.zip
