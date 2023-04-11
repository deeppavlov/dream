FROM python:3.9.16-slim

WORKDIR /src

ARG ASYNC_SIZE
ENV ASYNC_SIZE ${ASYNC_SIZE}

COPY ./annotators/news_api/requirements.txt requirements.txt
RUN pip install -r /src/requirements.txt && \
    python -c "import nltk; nltk.download('punkt')" && \
    python -m nltk.downloader vader_lexicon

COPY ./annotators/news_api/ ./
COPY ./common/ ./common/
COPY ./core ./core

CMD gunicorn --workers=1 server:app --bind 0.0.0.0:8000
