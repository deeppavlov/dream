FROM python:3.8.0

RUN mkdir /src
RUN mkdir /data

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./src/ /src

# ADD http://files.deeppavlov.ai/alexaprize_data/imdb_database_and_models.tar.gz /data/imdb_database_and_models.tar.gz
# RUN tar -zxvf /data/imdb_database_and_models.tar.gz -C /data/

WORKDIR /src

CMD gunicorn --workers=1 --bind 0.0.0.0:8023 --timeout=60 server:app
