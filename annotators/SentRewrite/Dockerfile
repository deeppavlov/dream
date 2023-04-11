FROM python:3.9.16-slim

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt

RUN pip install -r /src/requirements.txt && \
    python -c "import neuralcoref;" && \
    python -m spacy download en && \
    python -c "import nltk; nltk.download('punkt')"

COPY . /src/

CMD gunicorn --workers=1 server:app
