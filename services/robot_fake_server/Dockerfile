FROM python:3.9

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

RUN mkdir /src

COPY ./services/robot_fake_server/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./services/robot_fake_server /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=2 server:app