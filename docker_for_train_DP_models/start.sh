#!/bin/bash

cd "$(dirname "$0")"
# cd ..

workspace_dir=$PWD

# -v $workspace_dir/../data:/home/docker_current/data:rw \
# -v $workspace_dir/../py_files:/home/docker_current/py_files:rw \

desktop_start() {
    xhost +local:
    docker run -it -d --rm \
        --gpus all \
        --ipc host \
        --env="DISPLAY" \
        --env="QT_X11_NO_MITSHM=1" \
        --privileged \
        --name deeppavlov \
        -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
        -v $workspace_dir/../../:/home/docker_current:rw \
        ${ARCH}/deeppavlov:latest
    xhost -
}

arm_start() {
    xhost +local:
    docker run -it -d --rm \
        --runtime nvidia \
        --name deeppavlov \
        --network host \
        --env="DISPLAY" \
        -p 1025:1025 \
        --env="QT_X11_NO_MITSHM=1" \
        -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
        --privileged \
        -v $workspace_dir/../../:/home/docker_trajectronplusplus/catkin_ws/src:rw \
	    -v /home/jetson/tpp_ros/rosbags/:/home/docker_trajectronplusplus/catkin_ws/rosbags:rw \
        ${ARCH}/noetic/deeppavlov:latest
    xhost -
}


main () {
    if [ "$(docker ps -aq -f status=exited -f name=trajectronplusplus_ros1)" ]; then
        docker rm trajectronplusplus_ros1;
        echo the previous container has been deleted;
    fi

    ARCH="$(uname -m)"

    if [ "$ARCH" = "x86_64" ]; then
        desktop_start;
    elif [ "$ARCH" = "aarch64" ]; then
        arm_start;
    fi

}

main;
