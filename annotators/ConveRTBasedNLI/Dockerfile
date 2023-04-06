FROM python:3.7.4

ARG CONVERT_URL=http://files.deeppavlov.ai/tmp/nocontext_tf_model.tar.gz
ARG NLI_URL=http://files.deeppavlov.ai/tmp/model.h5
ARG TRAINED_MODEL_PATH

ENV TRAINED_MODEL_PATH ${TRAINED_MODEL_PATH}

COPY ${WORK_DIR}/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
COPY ${WORK_DIR} /src
WORKDIR /src

RUN mkdir /cache
RUN mkdir /data
RUN mkdir /data/nli_model/
RUN mkdir /data/convert_model/

RUN curl -L $NLI_URL --output /data/nli_model/model.h5
RUN curl -L $CONVERT_URL --output /tmp/conv_model.tar.gz && tar -xf /tmp/conv_model.tar.gz -C /data/convert_model && rm /tmp/conv_model.tar.gz
