FROM python:3.9.16-slim

WORKDIR /src

COPY ./skills/news_api_skill/requirements.txt requirements.txt
RUN pip install -r /src/requirements.txt && \
    python -c "import nltk; nltk.download('punkt')" && \
    python -m nltk.downloader vader_lexicon

COPY ./skills/news_api_skill/ ./
COPY ./common/ ./common/
COPY ./core ./core

CMD gunicorn --workers=1 server:app --bind 0.0.0.0:8000
