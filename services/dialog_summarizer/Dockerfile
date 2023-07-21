FROM python:3.7.4

ARG PRETRAINED_MODEL_NAME
ENV PRETRAINED_MODEL_NAME ${PRETRAINED_MODEL_NAME}

COPY ${WORK_DIR}/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
COPY ${WORK_DIR} /src
WORKDIR /src
