#!/bin/bash

usage() {
  echo "Usage: $0 --create|--delete"
  exit 1
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -d|--delete) d=1;;
        -c|--create) c=1;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$d" ] && [ -z "$c" ]; then
  usage
  exit 1
fi

if [ -n "$d" ] && [ -n "$c" ]; then
  usage
  exit 1
fi

#export AWS_ACCESS_KEY_ID='AKIAT2RXIFYZLDB66LZ3'
#export AWS_SECRET_ACCESS_KEY='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'
#export AWS_DEFAULT_REGION='us-east-1'
#export LB_NAME="a72bd67cd6eb54e188e4513c1f70ab0b"
export AWS_ACCESS_KEY_ID='AKIA5U27I4UTIJ7QJJ5L'
export AWS_SECRET_ACCESS_KEY='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'
export AWS_DEFAULT_REGION='us-west-2'
export LB_NAME="a737ad642c7cc4356a543c2c58779eb6"


SG=$(aws elb describe-load-balancers --load-balancer-name $LB_NAME --query LoadBalancerDescriptions[*].SecurityGroups[] --output text)

if [ -n "$d" ]; then
  aws ec2 revoke-security-group-ingress --group-id $SG --protocol tcp --port 80 --cidr 0.0.0.0/0
  aws ec2 revoke-security-group-ingress --group-id $SG --protocol tcp --port 443 --cidr 0.0.0.0/0
fi

if [ -n "$c" ]; then
  aws ec2 authorize-security-group-ingress --group-id $SG --protocol tcp --port 80 --cidr 0.0.0.0/0
  aws ec2 authorize-security-group-ingress --group-id $SG --protocol tcp --port 443 --cidr 0.0.0.0/0
fi
