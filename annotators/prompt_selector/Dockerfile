FROM python:3.9.16-slim

WORKDIR /src

COPY annotators/prompt_selector/requirements.txt /src/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache -r /src/requirements.txt

COPY ./annotators/prompt_selector/ /src/
COPY ./common/ /src/common/

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG SENTENCE_RANKER_SERVICE_URL
ENV SENTENCE_RANKER_SERVICE_URL ${SENTENCE_RANKER_SERVICE_URL}
ARG N_SENTENCES_TO_RETURN
ENV N_SENTENCES_TO_RETURN ${N_SENTENCES_TO_RETURN}

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD gunicorn --workers=1 server:app --bind 0.0.0.0:8000
