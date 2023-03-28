FROM python:3.7.4

ARG DATA_URL=http://files.deeppavlov.ai/tmp/nocontext_tf_model.tar.gz
ARG NEL_URL=http://files.deeppavlov.ai/tmp/model.h5

ENV CACHE_DIR /cache
ENV TRAINED_MODEL_PATH /data/nli_model/model.h5
ENV CONVERT_MODEL_PATH /data/convert_model

WORKDIR /src
RUN mkdir /cache

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir -p /data/nli_model/
RUN curl -L $NEL_URL --output /data/nli_model/model.h5

RUN mkdir -p /data/convert_model/
RUN curl -L $DATA_URL --output /tmp/conv_model.tar.gz && tar -xf /tmp/conv_model.tar.gz -C /data/convert_model && rm /tmp/conv_model.tar.gz

COPY . .
