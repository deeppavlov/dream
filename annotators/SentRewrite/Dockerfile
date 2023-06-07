FROM python:3.7.16-slim

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt

RUN pip install --upgrade pip && \
    pip install -r /src/requirements.txt && \
    python -m spacy download en && \
    python -c "import neuralcoref; import nltk; nltk.download('punkt')"

COPY . /src/

CMD gunicorn --workers=1 server:app
