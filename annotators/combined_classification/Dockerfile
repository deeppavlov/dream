FROM deeppavlov/deeppavlov:1.2.0-gpu

WORKDIR /base/DeepPavlov


WORKDIR /src
RUN mkdir common

COPY annotators/combined_classification/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

ARG SERVICE_PORT
ENV SERVICE_PORT=$SERVICE_PORT
ARG CONFIG
ENV CONFIG=$CONFIG
ARG KEEP_ZERO_CONFS=0
ENV KEEP_ZERO_CONFS=$KEEP_ZERO_CONFS

COPY annotators/combined_classification/ ./
COPY common/ common/

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200 --preload
