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
ARG PROMPTS_TO_CONSIDER
ENV PROMPTS_TO_CONSIDER ${PROMPTS_TO_CONSIDER}

CMD gunicorn --workers=1 server:app --bind 0.0.0.0:8000
