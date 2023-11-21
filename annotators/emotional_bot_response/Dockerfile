FROM python:3.9.16
WORKDIR /src

COPY annotators/emotional_bot_response/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

ARG SERVICE_PORT
ENV SERVICE_PORT=$SERVICE_PORT
ARG GENERATIVE_TIMEOUT
ENV GENERATIVE_TIMEOUT ${GENERATIVE_TIMEOUT}
ARG GENERATIVE_SERVICE_URL
ENV GENERATIVE_SERVICE_URL ${GENERATIVE_SERVICE_URL}
ARG GENERATIVE_SERVICE_CONFIG
ENV GENERATIVE_SERVICE_CONFIG ${GENERATIVE_SERVICE_CONFIG}
ARG N_UTTERANCES_CONTEXT
ENV N_UTTERANCES_CONTEXT ${N_UTTERANCES_CONTEXT}
ARG ENVVARS_TO_SEND
ENV ENVVARS_TO_SEND ${ENVVARS_TO_SEND}

COPY annotators/emotional_bot_response/ ./
COPY common /src/common

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change status to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=600