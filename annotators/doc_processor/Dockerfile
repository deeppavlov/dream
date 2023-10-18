FROM python:3.9.16
WORKDIR /src

COPY annotators/doc_processor/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN mkdir /data/

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG DOC_PATHS_OR_LINKS
ENV DOC_PATHS_OR_LINKS ${DOC_PATHS_OR_LINKS}
ARG FILE_SERVER_TIMEOUT=30
ENV FILE_SERVER_TIMEOUT ${FILE_SERVER_TIMEOUT}
ARG N_TURNS_TO_KEEP_DOC
ENV N_TURNS_TO_KEEP_DOC ${N_TURNS_TO_KEEP_DOC}

COPY annotators/doc_processor /src
COPY documents /src/documents
COPY common /src/common

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200
