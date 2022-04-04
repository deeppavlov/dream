FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN mkdir /data

WORKDIR /src

ARG INTENT_PHRASES_PATH
ENV INTENT_PHRASES_PATH ${INTENT_PHRASES_PATH}
ARG INTENTS_MODEL_PATH
ENV INTENTS_MODEL_PATH ${INTENTS_MODEL_PATH}
ARG TRANSFORMERS_MODEL_PATH
ENV TRANSFORMERS_MODEL_PATH ${TRANSFORMERS_MODEL_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}


RUN wget -c -q http://files.deeppavlov.ai/deeppavlov_data/${INTENTS_MODEL_PATH}.tar.gz -P /data/
RUN tar -xzf /data/${INTENTS_MODEL_PATH}.tar.gz -C /data/
RUN rm /data/${INTENTS_MODEL_PATH}.tar.gz

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('${TRANSFORMERS_MODEL_PATH}');"
RUN python -c "from transformers import AutoModelForSequenceClassification; AutoModelForSequenceClassification.from_pretrained('${TRANSFORMERS_MODEL_PATH}');"

COPY . /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
