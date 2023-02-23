FROM python:3.8.4

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG N_SENTENCES_TO_RETURN
ENV N_SENTENCES_TO_RETURN ${N_SENTENCES_TO_RETURN}
ARG PROMPTS_TO_CONSIDER
ENV PROMPTS_TO_CONSIDER ${PROMPTS_TO_CONSIDER}

RUN mkdir /src

COPY annotators/prompt_selector/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./annotators/prompt_selector/ /src/
COPY ./common/ /src/common/

WORKDIR /src

CMD gunicorn --workers=1 server:app --bind 0.0.0.0:8000
