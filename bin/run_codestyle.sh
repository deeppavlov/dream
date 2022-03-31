#!/usr/bin/env bash

pip3 install flake8

for ARGUMENT in "$@"; do

    KEY=$(echo $ARGUMENT | cut -f1 -d=)
    VALUE=$(echo $ARGUMENT | cut -f2 -d=)

    case "$KEY" in
    DIFF_BRANCH) DIFF_BRANCH=${VALUE} ;;
    *) ;;
    esac
done

if [[ "$DIFF_BRANCH" == "" ]]; then
    DIFF_BRANCH="dev"
fi

res=$(git diff --cached --name-only --diff-filter=ACMR origin/$DIFF_BRANCH | grep \.py\$ | tr -d "[:blank:]")
if [ -z "$res" ]
then
  exit 0
else
  flake8 --statistics --count $(git diff --cached --name-only --diff-filter=ACMR origin/$DIFF_BRANCH | grep \.py\$)
fi
