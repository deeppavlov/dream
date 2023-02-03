FROM python:3.9.1

ARG CONFIG
ARG COMMIT
ARG FAST=1
ARG PORT
ARG SRC_DIR
ARG LANGUAGE=EN
ENV LANGUAGE ${LANGUAGE}

ENV CONFIG=$CONFIG
ENV FAST=$FAST
ENV PORT=$PORT
ENV COMMIT=$COMMIT
ENV LANGUAGE=$LANGUAGE

COPY ./annotators/wiki_parser/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN pip install pybind11==2.2.4
RUN pip install hdt==2.3

ARG WIKI_LITE_DB
ENV WIKI_LITE_DB ${WIKI_LITE_DB}
ARG WIKI_LITE_INDEX_DB
ENV WIKI_LITE_INDEX_DB ${WIKI_LITE_INDEX_DB}
ARG WIKI_CACHE_DB
ENV WIKI_CACHE_DB ${WIKI_CACHE_DB}

RUN mkdir -p /root/.deeppavlov/downloads/wikidata
RUN wget -q -P /root/.deeppavlov/downloads/wikidata ${WIKI_LITE_DB}
RUN wget -q -P /root/.deeppavlov/downloads/wikidata ${WIKI_LITE_INDEX_DB}
RUN wget -q -P /root/.deeppavlov/downloads/wikidata ${WIKI_CACHE_DB}

COPY $SRC_DIR /src
WORKDIR /src
COPY ./common/ ./common/

CMD gunicorn  --workers=1 --timeout 500 --graceful-timeout 500 server:app -b 0.0.0.0:8077
