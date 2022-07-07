FROM python:3.9.1

ARG WORK_DIR

RUN mkdir /src
COPY ${WORK_DIR}/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN python -m spacy download en_core_web_sm
RUN python -m nltk.downloader wordnet

COPY common /src/common
COPY ${WORK_DIR} /src
WORKDIR /src

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD gunicorn --workers=1 server:app --reload
