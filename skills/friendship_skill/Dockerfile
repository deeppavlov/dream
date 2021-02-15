FROM python:3.9.1

WORKDIR /src

COPY ./skills/friendship_skill/requirements.txt .
RUN pip install -r requirements.txt

RUN python -m spacy download en
RUN python -m spacy download en_core_web_sm
RUN python -m nltk.downloader vader_lexicon

COPY ./skills/friendship_skill/programy_logger_off.sh ./programy_logger_off.sh

RUN bash programy_logger_off.sh

COPY ./skills/friendship_skill/ ./
COPY ./common/ ./common/

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1


CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}
