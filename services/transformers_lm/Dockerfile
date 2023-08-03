# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG LANGUAGE=EN
ENV LANGUAGE ${LANGUAGE}
ARG HALF_PRECISION
ENV HALF_PRECISION ${HALF_PRECISION}
ARG ADDITIONAL_EOS_TOKENS
ENV ADDITIONAL_EOS_TOKENS ${ADDITIONAL_EOS_TOKENS}


COPY ./services/transformers_lm/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY services/transformers_lm /src
COPY common /src/common

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
