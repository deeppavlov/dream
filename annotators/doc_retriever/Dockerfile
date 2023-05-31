FROM python:3.9.16
WORKDIR /src

ARG CONFIG_PATH
ENV CONFIG_PATH ${CONFIG_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG ORIGINAL_FILE_PATH
ENV ORIGINAL_FILE_PATH ${ORIGINAL_FILE_PATH}
ARG DATASET_PATH
ENV DATASET_PATH ${DATASET_PATH}

COPY annotators/doc_retriever/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt && python -c "import nltk; nltk.download('punkt')" && spacy download en_core_web_sm
RUN mkdir /data/

COPY annotators/doc_retriever /src
COPY documents /src/documents
COPY common /src/common

RUN python train_model_if_not_exist.py

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200
