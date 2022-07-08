FROM python:3.7.4

 RUN mkdir /src

 COPY ./requirements.txt /src/requirements.txt
 RUN pip install -r /src/requirements.txt

 COPY . /src/
 WORKDIR /src

 ARG DATA_URL=files.deeppavlov.ai/alexaprize_data/reddit_embeddings.pickle

 RUN mkdir /data
 RUN curl -L $DATA_URL --output /data/reddit_embeddings.pickle

 ENV DATABASE_PATH /data/reddit_embeddings.pickle

 CMD gunicorn --workers=2 server:app
