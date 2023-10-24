FROM python:3.10

RUN mkdir /src

COPY ./skill_selectors/universal_llm_based_skill_selector/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG DEFAULT_LM_SERVICE_TIMEOUT
ENV DEFAULT_LM_SERVICE_TIMEOUT ${DEFAULT_LM_SERVICE_TIMEOUT}
ARG N_UTTERANCES_CONTEXT=5
ENV N_UTTERANCES_CONTEXT ${N_UTTERANCES_CONTEXT}
ARG DEFAULT_LM_SERVICE_URL
ENV DEFAULT_LM_SERVICE_URL ${DEFAULT_LM_SERVICE_URL}
ARG DEFAULT_LM_SERVICE_CONFIG
ENV DEFAULT_LM_SERVICE_CONFIG ${DEFAULT_LM_SERVICE_CONFIG}

COPY skill_selectors/universal_llm_based_skill_selector /src
WORKDIR /src
COPY ./common/ ./common/
COPY ./components/ ./components/

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200
