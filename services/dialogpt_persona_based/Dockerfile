# syntax=docker/dockerfile:experimental

# FROM nvidia/cuda:11.6.0-devel-ubuntu18.04
FROM pytorch/pytorch:1.13.0-cuda11.6-cudnn8-runtime
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
	apt-get upgrade -y && \
	apt-get install -y git

RUN apt install software-properties-common -y && \
	add-apt-repository ppa:deadsnakes/ppa -y && \
	apt update && \
	apt install python3.10 -y

ENV VIRTUAL_ENV=/opt/venv
RUN python3 --version && \
	python3 -m venv $VIRTUAL_ENV && \
	$VIRTUAL_ENV/bin/pip install --upgrade pip && \
	$VIRTUAL_ENV/bin/pip install --upgrade setuptools
# RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG MAX_PERSONA_SENTENCES=3
ENV MAX_PERSONA_SENTENCES ${MAX_PERSONA_SENTENCES}

RUN python3 --version
RUN pip3 --version

COPY ./services/dialogpt_persona_based/requirements.txt /src/requirements.txt
COPY ./common/ /src/common/
RUN pip3 install -r /src/requirements.txt
RUN python3 -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('${PRETRAINED_MODEL_NAME_OR_PATH}');"
RUN python3 -c "from transformers import AutoModelForSeq2SeqLM; AutoModelForSeq2SeqLM.from_pretrained('${PRETRAINED_MODEL_NAME_OR_PATH}');"

COPY ./services/dialogpt_persona_based/ /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
