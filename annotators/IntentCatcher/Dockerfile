FROM tensorflow/tensorflow:1.14.0-py3

EXPOSE 8014:8014

WORKDIR /src
RUN mkdir /data
RUN mkdir /data/models

RUN  apt-get update \
  && apt-get install -y wget \
  && rm -rf /var/lib/apt/lists/*

COPY ./src/requirements.txt requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# COPY ./tfhub_model/ /root/tfhub_cache/

ENV TFHUB_CACHE_DIR='/root/tfhub_cache'
ENV USE_MODEL_PATH='https://tfhub.dev/google/universal-sentence-encoder/1'
ENV INTENT_DATA_PATH='/data/intent_data_h3.json'
ENV INTENT_PHRASES_PATH='/data/intent_phrases.json'
ENV INTENT_MODEL_PATH='/data/models/linear_classifier_h3.h5'

RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/linear_classifier_h3.h5 -q -P /data/models

RUN python -c "import tensorflow_hub as hub; model=hub.Module('$USE_MODEL_PATH')"

COPY ./src/ ./
COPY ./data/ /data

CMD gunicorn --workers=1 --name=catcher --bind 0.0.0.0:8014 --timeout=500 server:app
