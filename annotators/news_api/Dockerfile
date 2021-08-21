FROM python:3.7.4

WORKDIR /src

COPY ./annotators/news_api/requirements.txt requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"
RUN python -m nltk.downloader vader_lexicon

COPY ./annotators/news_api/ ./
COPY ./common/ ./common/
COPY ./core ./core

CMD gunicorn --workers=1 server:app --bind 0.0.0.0:8000
