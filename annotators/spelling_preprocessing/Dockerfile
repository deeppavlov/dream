FROM python:3.7.4

RUN mkdir /src

COPY annotators/spelling_preprocessing/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY annotators/spelling_preprocessing /src/
WORKDIR /src

CMD gunicorn --workers=2 server:app
