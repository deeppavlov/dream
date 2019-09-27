#!/usr/bin/env bash

pip install flake8==3.7.8

res=$(git diff --cached --name-only --diff-filter=ACMR dev | grep \.py\$ | tr -d "[:blank:]")
if [ -z "$res" ]
then
  exit 0
else
  flake8 --statistics --count $(git diff --cached --name-only --diff-filter=ACMR dev | grep \.py\$)
fi
