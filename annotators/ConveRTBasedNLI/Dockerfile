FROM python:3.7.4

RUN mkdir /src
WORKDIR /src

RUN mkdir /cache

COPY . .
RUN pip install -r requirements.txt

RUN wget 'https://github.com/davidalami/ConveRT/releases/download/1.0/nocontext_tf_model.tar.gz'
RUN mkdir /convert_model
RUN tar -xf nocontext_tf_model.tar.gz --directory /convert_model

ENV TRAINED_MODEL_PATH model.h5
ENV CACHE_DIR /cache
ENV CONVERT_MODEL_PATH /convert_model
