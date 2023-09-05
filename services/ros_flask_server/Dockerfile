FROM ubuntu:20.04

ARG SERVICE_PORT
ARG USERNAME=dkr
ARG USER_UID=1000
ARG USER_GID=$USER_UID

ENV SERVICE_PORT ${SERVICE_PORT}

RUN apt update

RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata keyboard-configuration

RUN apt install -y gnupg curl ca-certificates

COPY ./services/ros_flask_server/* /src/
COPY ./common/ /src/common/

SHELL ["/bin/bash", "-c"]

RUN apt update
RUN apt install -y lsb-release build-essential python3 gcc g++ make cmake git python-is-python3 apt-utils nginx

RUN apt install -y python3-pip
RUN pip install -r /src/requirements.txt

RUN apt install -y ufw

RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
RUN curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add -
RUN apt update
RUN apt install -y ros-noetic-desktop

RUN apt install -y python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool
RUN rosdep init
RUN rosdep update

WORKDIR /src/

CMD rm -rf /src/catkin_ws; mkdir -p /src/catkin_ws/src && cd catkin_ws && export PATH=/src/.local/bin:$PATH && source /opt/ros/noetic/setup.bash && catkin_make && source devel/setup.bash && cd src && catkin_create_pkg ros_dream std_msgs rospy roscpp && cd /src/catkin_ws && mkdir /src/catkin_ws/src/ros_dream/scripts && mv /src/listener.py /src/catkin_ws/src/ros_dream/scripts/listener.py && catkin_make && cd /src && source /src/catkin_ws/devel/setup.bash && (trap 'kill 0' SIGINT; roscore & gunicorn -b 0.0.0.0:$SERVICE_PORT --workers=1 server:app)