FROM tensorflow/tensorflow:1.14.0-py3

EXPOSE 8014:8014

ARG INTENT_MODEL_FNAME
ENV INTENT_MODEL_PATH='/data/models/'$INTENT_MODEL_FNAME
ARG USE_MODEL_PATH
ENV USE_MODEL_PATH=$USE_MODEL_PATH
ARG INTENT_DATA_FNAME
ENV INTENT_DATA_PATH='/data/'$INTENT_DATA_FNAME
ARG INTENT_PHRASES_FNAME
ENV INTENT_PHRASES_PATH='/data/'$INTENT_PHRASES_FNAME

ARG LANGUAGE=EN
ENV LANGUAGE ${LANGUAGE}

WORKDIR /src
RUN mkdir /data

RUN  apt-get update \
  && apt-get install -y wget \
  && rm -rf /var/lib/apt/lists/*

COPY ./src/requirements.txt requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# COPY ./tfhub_model/ /root/tfhub_cache/

ENV TFHUB_CACHE_DIR='/root/tfhub_cache'

RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/$INTENT_MODEL_FNAME -q -P /data/models

RUN python -c "import tensorflow_hub as hub; import tf_sentencepiece; import tensorflow as tf; config = tf.ConfigProto(); config.graph_options.rewrite_options.shape_optimization = 2; session = tf.Session(config=config); model=hub.Module('$USE_MODEL_PATH')"

COPY ./src/ ./
COPY ./data/ /data

CMD gunicorn --workers=1 --name=catcher --bind 0.0.0.0:8014 --timeout=500 server:app
