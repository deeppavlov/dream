FROM python:3.9.16-slim

ARG CONVERT_URL=http://files.deeppavlov.ai/tmp/convert_model.tar.gz
ARG NLI_URL=http://files.deeppavlov.ai/tmp/nli_model.tar.gz
ARG TRAINED_MODEL_PATH
ARG SERVICE_PORT

ENV TRAINED_MODEL_PATH ${TRAINED_MODEL_PATH}
ENV SERVICE_PORT ${SERVICE_PORT}

RUN apt-get update && \
    apt-get install -y --allow-unauthenticated wget && \
    rm -rf /var/lib/apt/lists/*

COPY ${WORK_DIR}/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
COPY ${WORK_DIR} /src
WORKDIR /src

RUN mkdir /cache /data /data/nli_model/ /data/convert_model/
RUN wget -c -q $NLI_URL -P /tmp/ && \
    tar -xf /tmp/nli_model.tar.gz -C /data/nli_model/ && \
    wget -c -q $CONVERT_URL -P /tmp/ && \
    tar -xf /tmp/convert_model.tar.gz -C /data/convert_model/ && \
    rm -rf /tmp/