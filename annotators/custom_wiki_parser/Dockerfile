FROM python:3.9.1

ARG PORT
ARG SRC_DIR

ENV PORT=$PORT

COPY ./annotators/custom_wiki_parser/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY $SRC_DIR /src
WORKDIR /src

CMD gunicorn  --workers=1 --timeout 500 --graceful-timeout 500 server:app -b 0.0.0.0:8132
