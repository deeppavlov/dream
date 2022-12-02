# syntax=docker/dockerfile:experimental

FROM nvidia/cuda:11.6.0-devel-ubuntu18.04
RUN apt-get update && \
	apt-get upgrade -y && \
	apt-get install -y git
RUN apt install software-properties-common -y && \
	add-apt-repository ppa:deadsnakes/ppa -y && \
	apt update && \
	apt install python3.10 -y

RUN apt-get install python3-pip -y

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG MAX_PERSONA_SENTENCES=3
ENV MAX_PERSONA_SENTENCES ${MAX_PERSONA_SENTENCES}


COPY ./services/dialogpt_persona_based/requirements.txt /src/requirements.txt
COPY ./common/ /src/common/
RUN pip install -r /src/requirements.txt

RUN python3.10 -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('${PRETRAINED_MODEL_NAME_OR_PATH}');"
RUN python3.10 -c "from transformers import AutoModelForSeq2SeqLM; AutoModelForSeq2SeqLM.from_pretrained('${PRETRAINED_MODEL_NAME_OR_PATH}');"

COPY ./services/dialogpt_persona_based/ /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
