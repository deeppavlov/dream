FROM python:3.7

WORKDIR /src

COPY ./annotators/speech_function_classifier/requirements.txt requirements.txt

RUN pip install -r requirements.txt

RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.0.0/en_core_web_sm-3.0.0.tar.gz

COPY ./annotators/speech_function_classifier/* ./
COPY ./common ./common

RUN python models.py

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
