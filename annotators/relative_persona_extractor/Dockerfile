FROM python:3.8.4

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG N_SENTENCES_TO_RETURN
ENV N_SENTENCES_TO_RETURN ${N_SENTENCES_TO_RETURN}

RUN mkdir /src

COPY annotators/relative_persona_extractor/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./annotators/relative_persona_extractor/ /src/
COPY ./common/ /src/common/

WORKDIR /src

CMD gunicorn --workers=1 server:app --bind 0.0.0.0:8000
