FROM python:3.9

ARG ROS_FLASK_SERVER
ENV ROS_FLASK_SERVER ${ROS_FLASK_SERVER}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

RUN mkdir /src

COPY ./services/robot_command_sender/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./services/robot_command_sender /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=2 server:app