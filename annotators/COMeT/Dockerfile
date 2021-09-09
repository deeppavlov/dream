# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.2-cuda10.0-cudnn7-runtime

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

ARG GRAPH
ARG PRETRAINED_MODEL
ARG PREPROCESS_DATA
ARG DECODING_ALGO
ARG SERVICE_NAME
ARG SERVICE_PORT

ENV GRAPH ${GRAPH}
ENV PRETRAINED_MODEL ${PRETRAINED_MODEL}
ENV DECODING_ALGO ${DECODING_ALGO}
ENV SERVICE_NAME ${SERVICE_NAME}
ENV SERVICE_PORT ${SERVICE_PORT}

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV PYTHONPATH /src/comet_commonsense/

WORKDIR /src

COPY server.py test_server.py test.sh requirements.txt ./
COPY comet_commonsense/ comet_commonsense/

RUN wget ${PRETRAINED_MODEL} -q -P /src/comet_commonsense/pretrained_models/

RUN wget ${PREPROCESS_DATA} -q -P /src/comet_commonsense/data/${GRAPH}/processed/generation/

RUN wget -c -q http://lnsigo.mipt.ru/export/alexaprize_data/comet/model.tar.gz \
    && tar -xzf model.tar.gz -C /src/comet_commonsense/ \
    && rm model.tar.gz

RUN pip install -r requirements.txt
RUN python -m spacy download en

 CMD uvicorn server:app --reload --host 0.0.0.0 --port ${SERVICE_PORT}
