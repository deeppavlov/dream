FROM python:3.10

RUN mkdir /data
WORKDIR /src

COPY ./services/openai_api_lm/requirements.txt /src/requirements.txt
RUN pip install --upgrade pip && pip install -r /src/requirements.txt

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG STATISTICS_FILES_PATH=stats/
ENV STATISTICS_FILES_PATH ${STATISTICS_FILES_PATH}

COPY services/openai_api_lm /src
COPY common /src/common

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
