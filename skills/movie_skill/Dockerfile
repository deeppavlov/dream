FROM python:3.8.0

WORKDIR /src

COPY ./skills/movie_skill/requirements.txt .
RUN pip install -r requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"

# ADD http://files.deeppavlov.ai/alexaprize_data/imdb_database_and_models.tar.gz /data/imdb_database_and_models.tar.gz
# RUN tar -zxvf /data/imdb_database_and_models.tar.gz -C /data/

COPY ./skills/movie_skill ./
COPY ./common/ common/

CMD gunicorn --workers=1 --bind 0.0.0.0:8023 --timeout=60 server:app --preload
