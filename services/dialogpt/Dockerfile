# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG CONFIG_NAME
ENV CONFIG_NAME ${CONFIG_NAME}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG N_HYPOTHESES_TO_GENERATE
ENV N_HYPOTHESES_TO_GENERATE ${N_HYPOTHESES_TO_GENERATE}

COPY ./services/dialogpt/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./services/dialogpt/ /src/
COPY ./common/ ./common/

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200
