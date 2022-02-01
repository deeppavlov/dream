FROM python:3.7.4

RUN mkdir /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN spacy download en_core_web_sm
RUN spacy download ru_core_news_sm

COPY . /src/
WORKDIR /src

CMD gunicorn --workers=2 server:app
