FROM deeppavlov/deeppavlov:1.2.0-gpu

WORKDIR /src

ARG CONFIG_NAME
ENV CONFIG_NAME ${CONFIG_NAME}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG INTENT_PHRASES_PATH
ENV INTENT_PHRASES_PATH ${INTENT_PHRASES_PATH}

COPY annotators/IntentCatcherTransformers/requirements.txt /src/requirements.txt
RUN pip install --upgrade pip && pip install -r /src/requirements.txt

COPY ./common/ ./common/
COPY annotators/IntentCatcherTransformers/ /src
WORKDIR /src

RUN python -m deeppavlov download ${CONFIG_NAME} && \
    python train_model_if_not_exist.py


CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200
