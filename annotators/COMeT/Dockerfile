# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.2-cuda10.0-cudnn7-runtime

RUN apt-get update && apt-get install -y --allow-unauthenticated git wget && rm -rf /var/lib/apt/lists/*

ARG GRAPH
ENV GRAPH ${GRAPH}
ARG PRETRAINED_MODEL
ENV PRETRAINED_MODEL ${PRETRAINED_MODEL}
ARG PREPROCESS_DATA
ENV PREPROCESS_DATA ${PREPROCESS_DATA}
ARG TEST_SCRIPT
ENV TEST_SCRIPT ${TEST_SCRIPT}

WORKDIR /comet

RUN git clone https://github.com/atcbosselut/comet-commonsense.git .
RUN git reset --hard de71afa4407816033320b91ae458216329a35fa8

WORKDIR /comet/pretrained_models
RUN wget ${PRETRAINED_MODEL} -q

WORKDIR /comet/data/${GRAPH}/processed/generation/
RUN wget ${PREPROCESS_DATA} -q

WORKDIR /comet
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/comet/model.tar.gz -q
RUN tar -xvzf model.tar.gz
RUN rm model.tar.gz

WORKDIR /comet

COPY ./requirements.txt /comet/requirements.txt
RUN pip install -r /comet/requirements.txt
RUN python -m spacy download en

COPY . /comet/
WORKDIR /comet

# apply patch to:
# 1. fix error in src/interactive/functions.py
# 2. remove unnecessary prints
# 3. allow to pass tuples as category
RUN git apply /comet/functions.diff

ARG DECODING_ALGO
ENV DECODING_ALGO ${DECODING_ALGO}

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8053
