# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

RUN mkdir /data/

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200

