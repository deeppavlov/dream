FROM python:3.7.4

RUN mkdir /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./download_flair_model.py /src/download_flair_model.py
RUN python /src/download_flair_model.py
# COPY ~/.flair/models/en-ner-ontonotes-v0.4.pt ~/models/en-ner-ontonotes-v0.4.pt

COPY . /src/
WORKDIR /src


CMD gunicorn --workers=1 server:app --preload
