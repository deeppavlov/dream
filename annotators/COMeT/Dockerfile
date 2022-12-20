# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.4-cuda10.1-cudnn7-runtime

ARG GRAPH
ARG PRETRAINED_MODEL
ARG PREPROCESS_DATA
ARG DECODING_ALGO
ARG SERVICE_NAME
ARG SERVICE_PORT
ARG SERVICE_HOME

ENV GRAPH ${GRAPH}
ENV PRETRAINED_MODEL ${PRETRAINED_MODEL}
ENV DECODING_ALGO ${DECODING_ALGO}
ENV SERVICE_NAME ${SERVICE_NAME}
ENV SERVICE_PORT ${SERVICE_PORT}
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV PYTHONPATH /src/comet_commonsense/

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

COPY ./annotators/COMeT/requirements.txt /src/requirements.txt

RUN pip install -r /src/requirements.txt && \
    python -m spacy download en

COPY $SERVICE_HOME/ /src/
COPY ./common/ /src/common/
WORKDIR /src

RUN mkdir /data/
RUN mkdir /data/models/
RUN mkdir /data/comet_commonsense/

RUN wget -c -q http://lnsigo.mipt.ru/export/alexaprize_data/comet/model.tar.gz -P /data/models/ && \
    tar -xzf /data/models/model.tar.gz -C /data/comet_commonsense/ && \
    rm -rf /data/models/

RUN wget ${PRETRAINED_MODEL} -q -P /data/comet_commonsense/pretrained_models/ && \
    wget ${PREPROCESS_DATA} -q -P /data/comet_commonsense/data/${GRAPH}/processed/generation/

WORKDIR /src

CMD uvicorn server:app --host 0.0.0.0 --port ${SERVICE_PORT}
