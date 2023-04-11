FROM python:3.9.16-slim

WORKDIR /src

COPY ./requirements.txt requirements.txt
RUN pip install -r /src/requirements.txt && \
    python -m spacy download en_core_web_sm

COPY . .

CMD gunicorn --workers=2 server:app
