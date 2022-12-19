# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

WORKDIR /src

ARG MODEL_URL
ENV MODEL_URL ${MODEL_URL}

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN mkdir /data
RUN wget ${MODEL_URL} -q -O /data/model.pth

COPY . /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8079
