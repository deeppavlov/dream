FROM python:3.7

WORKDIR /src

COPY annotators/speech_function_predictor/requirements.txt requirements.txt

RUN pip install -r requirements.txt

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

COPY ./* ./
