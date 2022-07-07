FROM python:3.6

RUN mkdir /src
RUN mkdir /data
RUN mkdir /src/common

COPY ./skills/reddit_ner_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/reddit_ner_skill/ /src/
COPY ./common/ /src/common/

ADD http://files.deeppavlov.ai/alexaprize_data/reddit_ner_skill/entity_database.json /data/entity_database.json
ADD http://files.deeppavlov.ai/alexaprize_data/reddit_ner_skill/posts.json /data/posts.json
ADD http://files.deeppavlov.ai/alexaprize_data/reddit_ner_skill/phrases.json /data/phrases.json

WORKDIR /src

EXPOSE 8035:8035

CMD gunicorn --workers=1 --name=reddit_ner_skill --bind 0.0.0.0:8035 --timeout=500 server:app
