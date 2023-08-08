FROM python:3.10

WORKDIR /src

COPY ./services/anthropic_api_lm/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}

COPY services/anthropic_api_lm /src
COPY common /src/common

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
