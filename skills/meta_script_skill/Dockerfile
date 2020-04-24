FROM python:3.7.4

RUN mkdir /src
RUN mkdir /src/common

COPY ./skills/meta_script_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -m spacy download en
RUN python -m nltk.downloader vader_lexicon

COPY ./skills/meta_script_skill/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=2 server:app
