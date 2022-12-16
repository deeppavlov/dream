FROM python:3.6

RUN mkdir /src
RUN mkdir /data
RUN mkdir /src/common

COPY ./skills/reddit_ner_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/short_story_skill/ /src/
COPY ./common/ /src/common/

COPY ./skills/short_story_skill/phrases.json /data/phrases.json
COPY ./skills/short_story_skill/stories.json /data/stories.json

WORKDIR /src

EXPOSE 8057:8057

CMD gunicorn --workers=1 --name=short_story_skill --bind 0.0.0.0:8057 --timeout=1200 server:app
