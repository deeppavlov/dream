#!/bin/bash

# change current directory to executable script directory
cd "$(dirname "$0")"
cd ../..

for skill in $( ls  skills | grep -e 'dff.*skill' | sed 's/_/-/g' ); do
    docker-compose -f docker-compose.yml -f local.yml exec $skill bash test.sh
done

