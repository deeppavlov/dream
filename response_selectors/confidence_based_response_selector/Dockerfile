FROM python:3.10

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

ARG LANGUAGE=EN
ENV LANGUAGE ${LANGUAGE}
ARG FILTER_BADLISTED_WORDS
ENV FILTER_BADLISTED_WORDS ${FILTER_BADLISTED_WORDS}

COPY . /src/

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD gunicorn --workers=1 --bind 0.0.0.0:3003 server:app
