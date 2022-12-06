# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

RUN : \
	&& apt-get update \
	&& DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
	software-properties-common \
	&& add-apt-repository -y ppa:deadsnakes \
	&& DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
	python3.8-venv \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* \
	&& :

RUN apt-get update && \
	apt-get upgrade -y && \
	apt-get install -y git libsqlite3-dev

RUN python3.8 -m venv /venv
ENV PATH=/venv/bin:$PATH

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG MAX_PERSONA_SENTENCES=3
ENV MAX_PERSONA_SENTENCES ${MAX_PERSONA_SENTENCES}


RUN python --version

COPY ./services/dialogpt_persona_based/requirements.txt /src/requirements.txt
COPY ./common/ /src/common/

RUN pip install -r /src/requirements.txt --ignore-installed PyYAML

RUN python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('${PRETRAINED_MODEL_NAME_OR_PATH}');"
RUN python -c "from transformers import AutoModelForSeq2SeqLM; AutoModelForSeq2SeqLM.from_pretrained('${PRETRAINED_MODEL_NAME_OR_PATH}');"

COPY ./services/dialogpt_persona_based/ /src
# https://github.com/NVIDIA/nvidia-docker/issues/533
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV NVIDIA_VISIBLE_DEVICES=all

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
