# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

RUN : \
	&& apt-get update \
	&& DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
	software-properties-common \
	&& add-apt-repository -y ppa:deadsnakes \
	&& DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
	python3.10 \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* \
	&& :

RUN apt-get update && \
	apt-get upgrade -y && \
	apt-get install -y git libsqlite3-dev

RUN apt-get install python3.10-venv -y
RUN python3.10 -m venv /venv
ENV PATH=/venv/bin:$PATH
RUN python3.10 --version
WORKDIR /src

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG PAIR_DIALOG_HISTORY_LENGTH
ENV PAIR_DIALOG_HISTORY_LENGTH ${PAIR_DIALOG_HISTORY_LENGTH}
ARG CHAT_EVERY_SENT_MAX_LENGTH
ENV CHAT_EVERY_SENT_MAX_LENGTH ${CHAT_EVERY_SENT_MAX_LENGTH}
ARG PERSONA_EVERY_SENT_MAX_LENGTH
ENV PERSONA_EVERY_SENT_MAX_LENGTH ${PERSONA_EVERY_SENT_MAX_LENGTH}
ARG GENERATION_PARAMS_CONFIG
ENV GENERATION_PARAMS_CONFIG ${GENERATION_PARAMS_CONFIG}

COPY ./services/seq2seq_persona_based/requirements.txt /src/requirements.txt
# RUN --mount=type=cache,target=/root/.cache pip install -r /src/requirements.txt 
RUN pip install -r /src/requirements.txt 

COPY ./common/ /src/common/

COPY ./services/seq2seq_persona_based/ /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
