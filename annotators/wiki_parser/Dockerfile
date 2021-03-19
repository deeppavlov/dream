FROM python:3.9.1

ARG CONFIG
ARG COMMIT
ARG PORT
ARG SRC_DIR

ENV CONFIG=$CONFIG
ENV PORT=$PORT
ENV COMMIT=$COMMIT

COPY ./annotators/wiki_parser/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN pip install pybind11==2.2.4
RUN pip install hdt==2.3

RUN mkdir -p /root/.deeppavlov/downloads/wikidata
RUN wget -q -P /root/.deeppavlov/downloads/wikidata http://files.deeppavlov.ai/kbqa/wikidata/wikidata_lite.hdt
RUN wget -q -P /root/.deeppavlov/downloads/wikidata http://files.deeppavlov.ai/kbqa/wikidata/wikidata_lite.hdt.index.v1-1

COPY $SRC_DIR /src
WORKDIR /src

CMD gunicorn  --workers=1 --timeout 500 --graceful-timeout 500 server:app -b 0.0.0.0:8077
