# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG CONFIG_NAME
ENV CONFIG_NAME ${CONFIG_NAME}


COPY ./services/chatgpt/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

FROM ubuntu:18.04

RUN apt-get update && \
      apt-get -y install sudo

RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
USER docker

# CMD /bin/bash
RUN sudo apt install xvfb

COPY . /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
