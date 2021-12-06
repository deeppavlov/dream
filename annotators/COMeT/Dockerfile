# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.4-cuda10.1-cudnn7-runtime

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

ARG SERVICE_HOME

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV PYTHONPATH /src/comet_commonsense/

WORKDIR /src

COPY $SERVICE_HOME/requirements.txt ./

RUN pip install -r requirements.txt && \
    python -m spacy download en

COPY $SERVICE_HOME/comet_commonsense comet_commonsense

RUN wget -c -q http://lnsigo.mipt.ru/export/alexaprize_data/comet/model.tar.gz -P /src/models/ && \
    tar -xzf /src/models/model.tar.gz -C /src/comet_commonsense/ && \
    rm -rf /src/models/

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

RUN wget ${PRETRAINED_MODEL} -q -P /src/comet_commonsense/pretrained_models/ && \
    wget ${PREPROCESS_DATA} -q -P /src/comet_commonsense/data/${GRAPH}/processed/generation/

COPY $SERVICE_HOME/server.py $SERVICE_HOME/test_server.py $SERVICE_HOME/test.sh ./
COPY $SERVICE_HOME/tests tests
COPY ./common/ /src/common/

CMD uvicorn server:app --host 0.0.0.0 --port ${SERVICE_PORT}
