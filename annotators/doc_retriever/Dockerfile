FROM python:3.9.16
WORKDIR /src

COPY annotators/doc_retriever/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt && python -c "import nltk; nltk.download('punkt')" && spacy download en_core_web_sm
RUN mkdir /data/

ARG CONFIG_PATH
ENV CONFIG_PATH ${CONFIG_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG PARAGRAPHS_NUM
ENV PARAGRAPHS_NUM ${PARAGRAPHS_NUM}
ARG FILE_SERVER_TIMEOUT
ENV FILE_SERVER_TIMEOUT ${FILE_SERVER_TIMEOUT}

COPY annotators/doc_retriever /src
COPY documents /src/documents
COPY common /src/common

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200
