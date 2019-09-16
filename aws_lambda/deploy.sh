#!/usr/bin/env bash

# https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html
pip3 install -r aws_lambda/requirements.txt --target aws_lambda/package
cp aws_lambda/main.py aws_lambda/package/
cd aws_lambda/package && zip -r9 dp_agent_lambda.zip . && cd ../..
aws lambda update-function-code --function-name dp_agent_lambda_proxy --zip-file fileb://aws_lambda/package/dp_agent_lambda.zip
