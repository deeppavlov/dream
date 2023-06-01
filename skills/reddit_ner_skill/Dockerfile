FROM python:3.6

RUN apt-get update && \
    apt-get install -y --allow-unauthenticated wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN mkdir /data /src/common

COPY ./skills/reddit_ner_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/reddit_ner_skill/ /src/
COPY ./common/ /src/common/

RUN wget http://files.deeppavlov.ai/alexaprize_data/reddit_ner_skill/entity_database.json -q -O /data/entity_database.json && \
    wget http://files.deeppavlov.ai/alexaprize_data/reddit_ner_skill/posts.json -q -O /data/posts.json && \
    wget http://files.deeppavlov.ai/alexaprize_data/reddit_ner_skill/phrases.json -q -O /data/phrases.json


EXPOSE 8035:8035

CMD gunicorn --workers=1 --name=reddit_ner_skill --bind 0.0.0.0:8035 --timeout=500 server:app
