#!/bin/bash

cd "$(dirname "$0")"
# cd ..

# --env="DISPLAY" \

workspace_dir=$PWD

desktop_start() {
    xhost +local:
    docker run -it -d --rm \
        --gpus all \
        --ipc host \
        --network host \
        --env="DISPLAY=$DISPLAY" \
        -v "$HOME/.Xauthority:/root/.Xauthority:ro" \
        --env="QT_X11_NO_MITSHM=1" \
        --privileged \
        --name test_dream \
        -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
        -v $workspace_dir/tests/:/home/docker_robot/tests:rw \
        ${ARCH}/noetic/test_dream:latest
    xhost -
}

arm_start() {
    xhost +local:
    docker run -it -d --rm \
        --runtime nvidia \
        --name robot_voice_navigation \
        --network host \
        -v "$HOME/.Xauthority:/root/.Xauthority:ro" \
        --env="DISPLAY" \
        -p 1025:1025 \
        --env="QT_X11_NO_MITSHM=1" \
        -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
        --privileged \
        -v $workspace_dir/../../:/home/docker_robot/catkin_ws/src:rw \
	    -v /home/jetson/tpp_ros/rosbags/:/home/docker_robot/catkin_ws/rosbags:rw \
        ${ARCH}/noetic/robot_voice_navigation:latest
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
