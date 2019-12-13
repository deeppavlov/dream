FROM python:3.7.4
RUN mkdir src
RUN mkdir global_data
COPY ./skills/tfidf_retrieval/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src
COPY ./tests/dream/test_dialogs_gold_phrases.csv /global_data/gold_phrases.csv
WORKDIR /src

CMD gunicorn --workers=2 server:app
