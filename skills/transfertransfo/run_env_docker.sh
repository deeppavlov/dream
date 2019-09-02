#!/bin/bash

# change current directory to executable script directory
cd "$(dirname "$0")"

docker build -t transfertransfo .


docker run -ti --rm -p 8888:8000 --name transfertransfo transfertransfo:latest