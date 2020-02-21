FROM tensorflow/tensorflow:1.14.0-py3

RUN mkdir /src
RUN mkdir /data

RUN  apt-get update \
  && apt-get install -y wget \
  && rm -rf /var/lib/apt/lists/*

COPY ./src/requirements.txt /src/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /src/requirements.txt

# COPY ./tfhub_model/ /root/tfhub_cache/

ENV TFHUB_CACHE_DIR='/root/tfhub_cache'
ENV USE_MODEL_PATH='https://tfhub.dev/google/universal-sentence-encoder/1'

RUN python -c "import tensorflow_hub as hub; model=hub.Module('$USE_MODEL_PATH')"

COPY ./src/ /src
COPY ./data/ /data

ADD http://files.deeppavlov.ai/alexaprize_data/intent_data_v20.json /data/classifier_data/intent_data.json

WORKDIR /src

EXPOSE 8014:8014

CMD gunicorn --workers=1 --name=catcher --bind 0.0.0.0:8014 --timeout=500 server:app
