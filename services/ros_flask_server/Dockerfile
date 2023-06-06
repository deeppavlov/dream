FROM ubuntu:20.04

ARG SERVICE_PORT
ARG USERNAME=dkr
ARG USER_UID=1000
ARG USER_GID=$USER_UID

ENV SERVICE_PORT ${SERVICE_PORT}

RUN apt update

RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata keyboard-configuration

RUN groupadd --gid $USER_GID $USERNAME && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME && apt update && apt install -y sudo && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME && chmod 0440 /etc/sudoers.d/$USERNAME

RUN apt install -y gnupg curl ca-certificates

RUN grep -E 'sudo|wheel' /etc/group

COPY ./services/ros_flask_server/* /home/$USERNAME/
COPY ./common/ /home/$USERNAME/common/

USER $USERNAME

SHELL ["/bin/bash", "-c"]

RUN sudo apt update
RUN sudo apt install -y lsb-release build-essential python3 gcc g++ make cmake git python-is-python3 apt-utils nginx

RUN sudo apt install -y python3-pip
RUN sudo pip install -r /home/$USERNAME/requirements.txt

RUN sudo apt install -y ufw

RUN sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
RUN curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
RUN sudo apt update
RUN sudo apt install -y ros-noetic-desktop

RUN source /opt/ros/noetic/setup.bash
RUN echo "export PATH=/home/dkr/.local/bin:$PATH" >> /home/$USERNAME/.bashrc
RUN echo "source /opt/ros/noetic/setup.bash" >> /home/$USERNAME/.bashrc
RUN source /home/$USERNAME/.bashrc

RUN echo /home/$USERNAME/.bashrc

RUN sudo apt install -y python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool
RUN sudo rosdep init
RUN rosdep update

RUN cat /home/$USERNAME/.bashrc

#RUN sudo chmod +x /home/$USERNAME/launch.sh

RUN mkdir -p /home/$USERNAME/catkin_ws/src
RUN touch /home/$USERNAME/catkin_init.sh
RUN echo "cd ~/catkin_ws && catkin_make && source devel/setup.bash && echo $ROS_PACKAGE_PATH && cd ~/catkin_ws/src && catkin_create_pkg ros_dream std_msgs rospy roscpp && cd ~/catkin_ws && catkin_make && source ~/catkin_ws/devel/setup.bash && source ~/.bashrc && mkdir ~/catkin_ws/src/ros_dream/scripts && mv ~/listener.py ~/catkin_ws/src/ros_dream/scripts/listener.py && cd ~/catkin_ws && catkin_make && cd ~ && source ~/catkin_ws/devel/setup.bash && roscore" >> /home/$USERNAME/catkin_init.sh

RUN sudo chmod +x /home/$USERNAME/catkin_init.sh

RUN echo "source /home/dkr/catkin_ws/devel/setup.bash" >> /home/$USERNAME/.bashrc
RUN source /home/$USERNAME/.bashrc

WORKDIR /home/$USERNAME/

CMD gunicorn -b 0.0.0.0:$SERVICE_PORT --workers=1 server:app
#CMD (trap 'kill 0' SIGINT; ./catkin_init.sh && roscore & gunicorn --workers=1 server:app)