FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

EXPOSE 8014:8014

WORKDIR /src
RUN mkdir /data

WORKDIR /src


ARG INTENT_PHRASES_PATH="intent_phrases.json"
ENV INTENT_PHRASES_PATH ${INTENT_PHRASES_PATH}
ARG INTENTS_MODEL_PATH="/data/intent_model_v0"
ENV INTENTS_MODEL_PATH ${INTENTS_MODEL_PATH}
ARG TRANSFORMERS_MODEL_PATH="distilbert-base-uncased"
ENV TRANSFORMERS_MODEL_PATH ${TRANSFORMERS_MODEL_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN python -c 'from transformers import AutoTokenizer; AutoTokenizer.from_pretrained("$TRANSFORMERS_MODEL_PATH");'
RUN python -c 'from transformers import AutoModelForSequenceClassification; AutoModelForSequenceClassification.from_pretrained("$TRANSFORMERS_MODEL_PATH");'

COPY . /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
