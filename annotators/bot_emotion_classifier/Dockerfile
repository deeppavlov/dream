FROM python:3.9.16
WORKDIR /src

COPY annotators/bot_emotion_classifier/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

ARG SERVICE_PORT
ENV SERVICE_PORT=$SERVICE_PORT

COPY annotators/bot_emotion_classifier/ ./
COPY common /src/common
RUN python -c 'import stanza; stanza.download("en")'

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change status to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=600