#!/bin/bash

yellow=`tput setaf 3`
reset_color=`tput sgr0`

ARCH="$(uname -m)"

main () {
    pushd "$(dirname "$0")";
    if [ "$ARCH" = "x86_64" ] || [ "$ARCH" = "aarch64" ]; then
        file="./Dockerfile.${ARCH}"
    else
        echo "There is no Dockerfile for ${yellow}${ARCH}${reset_color} arch"
    fi
    echo "Building image for ${yellow}${ARCH}${reset_color} arch. from Dockerfile: ${yellow}${file}${reset_color}"
    # docker build -f ${file} . -t ${ARCH}/noetic/trajectronplusplus:latest;

    docker build . \
        -f ${file} \
        --build-arg UID=$(id -u) \
        --build-arg GID=$(id -g) \
        --build-arg NUM_THREADS=${NUM_THREADS} \
        -t ${ARCH}/deeppavlov:latest
    popd;
}

main "$@"; exit;





