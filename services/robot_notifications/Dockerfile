FROM python:3.9

ARG ROS_FSM_SERVER
ENV ROS_FSM_SERVER ${ROS_FSM_SERVER}

RUN mkdir /src

COPY ./services/robot_notifications/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./services/robot_notifications /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=2 server:app