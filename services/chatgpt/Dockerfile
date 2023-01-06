# syntax=docker/dockerfile:experimental

FROM ubuntu:18.04

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG CONFIG_NAME
ENV CONFIG_NAME ${CONFIG_NAME}

COPY . /src

COPY requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN apt-get update && \
      apt-get -y install sudo

RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
USER docker

CMD ["/bin/bash","-c","/src/startup.sh"]
# CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
