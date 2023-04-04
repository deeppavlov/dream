FROM python:3.8.4

WORKDIR /src

COPY ./annotators/spacy_nounphrases/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./annotators/spacy_nounphrases/ /src/
COPY ./common/ /src/common/


CMD gunicorn --workers=2 server:app
