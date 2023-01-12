# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.4-cuda10.1-cudnn7-devel

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG CONFIG_NAME
ENV CONFIG_NAME ${CONFIG_NAME}


COPY ./services/gpt-3.5/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
