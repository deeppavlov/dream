# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.2-cuda10.0-cudnn7-runtime

RUN apt-get update && apt-get install -y --allow-unauthenticated git wget && rm -rf /var/lib/apt/lists/*

ARG GRAPH
ARG PRETRAINED_MODEL
ARG PREPROCESS_DATA
ARG TEST_SCRIPT
ARG DECODING_ALGO

ENV DECODING_ALGO ${DECODING_ALGO}
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

WORKDIR /comet

RUN git clone https://github.com/Arsenaut/comet-commonsense.git .

COPY server.py ${TEST_SCRIPT} test.sh requirements.txt ./

RUN wget ${PRETRAINED_MODEL} -q -P /comet/pretrained_models/

RUN wget ${PREPROCESS_DATA} -q -P /comet/data/${GRAPH}/processed/generation/

RUN wget -c -q http://lnsigo.mipt.ru/export/alexaprize_data/comet/model.tar.gz \
    && tar -xzf model.tar.gz \
    && rm model.tar.gz

RUN pip install -r requirements.txt
RUN python -m spacy download en
