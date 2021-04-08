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

export AWS_ACCESS_KEY_ID='AKIAT2RXIFYZLDB66LZ3'
export AWS_SECRET_ACCESS_KEY='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'
export AWS_DEFAULT_REGION='us-east-1'

if [ -n "$d" ]; then
  eksctl delete nodegroup -f cluster-alexa.yaml --include="ng2-gpu*,ng5-cpu" --approve
fi

if [ -n "$c" ]; then
  eksctl create nodegroup -f cluster-alexa.yaml --include="ng2-gpu*,ng5-cpu"
fi
