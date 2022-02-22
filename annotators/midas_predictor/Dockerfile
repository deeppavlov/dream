# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.4-cuda10.1-cudnn7-runtime

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /src/requirements.txt

RUN pip install -r /src/requirements.txt

COPY ./ /src/
COPY ./common/ /src/common/
WORKDIR /src

RUN mkdir /data/

ARG SERVICE_NAME
ARG SERVICE_PORT

ENV SERVICE_NAME ${SERVICE_NAME}
ENV SERVICE_PORT ${SERVICE_PORT}

WORKDIR /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8121
