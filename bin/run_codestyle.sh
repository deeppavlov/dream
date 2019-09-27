#!/usr/bin/env bash

pip install flake8==3.7.8

flake8 --statistics --count $(git diff --cached --name-only --diff-filter=ACMR dev | grep \.py\$)
