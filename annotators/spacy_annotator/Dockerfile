FROM python:3.8.4

ARG SRC_DIR
ENV SRC_DIR ${SRC_DIR}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG SPACY_MODEL
ENV SPACY_MODEL ${SPACY_MODEL}

RUN mkdir /src

COPY $SRC_DIR /src/
COPY ./common/ /src/common/

COPY $SRC_DIR/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -m spacy download ${SPACY_MODEL}

WORKDIR /src

CMD gunicorn --workers=2 server:app
