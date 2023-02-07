FROM python:3.7.4

ARG DATA_URL=https://github.com/davidalami/ConveRT/releases/download/1.0/nocontext_tf_model.tar.gz
ARG NEL_URL=https://github.com/Kolpnick/dream/blob/convert_based_nli/annotators/ConveRTBasedNLI/model.h5

ENV CACHE_DIR /cache
ENV TRAINED_MODEL_PATH /data/nli_model/model.h5
ENV CONVERT_MODEL_PATH /data/convert_model

WORKDIR /src
RUN mkdir /cache

RUN mkdir -p /data/nli_model/
RUN curl -L $NEL_URL --output /data/nli_model/model.h5

RUN mkdir -p /data/convert_model/
RUN curl -L $DATA_URL --output /tmp/conv_model.tar.gz && tar -xf /tmp/conv_model.tar.gz -C /data/convert_model && rm /tmp/conv_model.tar.gz

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
