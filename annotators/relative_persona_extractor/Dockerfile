FROM python:3.9.16-slim

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG SENTENCE_RANKER_SERVICE_URL
ENV SENTENCE_RANKER_SERVICE_URL ${SENTENCE_RANKER_SERVICE_URL}
ARG N_SENTENCES_TO_RETURN
ENV N_SENTENCES_TO_RETURN ${N_SENTENCES_TO_RETURN}

WORKDIR /src

COPY annotators/relative_persona_extractor/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./annotators/relative_persona_extractor/ /src/
COPY ./common/ /src/common/


CMD gunicorn --workers=1 server:app --bind 0.0.0.0:8000
