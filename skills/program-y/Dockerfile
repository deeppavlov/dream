FROM python:3.8

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

ARG RANDOM_SEED
ENV RANDOM_SEED ${RANDOM_SEED:-2718}

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

WORKDIR /src

COPY ./skills/${SERVICE_NAME}/requirements.txt .
RUN pip install -r requirements.txt

COPY ./skills/${SERVICE_NAME}/ ./
COPY ./common/ ./common
COPY ./state_formatters ./state_formatters

HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}