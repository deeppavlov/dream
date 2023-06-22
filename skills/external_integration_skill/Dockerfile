FROM python:3.7.4

WORKDIR /src

COPY ./skills/external_integration_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG ENVVARS_TO_SEND
ENV ENVVARS_TO_SEND ${ENVVARS_TO_SEND}

COPY skills/external_integration_skill /src
COPY common /src/common

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
