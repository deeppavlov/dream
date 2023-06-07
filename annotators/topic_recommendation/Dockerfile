FROM python:3.9.16-slim

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt

RUN pip install -r /src/requirements.txt

COPY . /src/

ARG DATA_URL=files.deeppavlov.ai/alexaprize_data/reddit_embeddings.pickle

RUN mkdir /data
RUN apt-get update && \
    apt-get install -y curl && \
    curl -L $DATA_URL --output /data/reddit_embeddings.pickle

ENV DATABASE_PATH /data/reddit_embeddings.pickle

CMD gunicorn --workers=2 server:app
