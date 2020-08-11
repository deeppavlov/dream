FROM python:3.8.0

RUN mkdir /src
COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.2.0/en_core_web_sm-2.2.0.tar.gz
COPY ./ /src/
WORKDIR /src

CMD gunicorn --workers=2 server:app
