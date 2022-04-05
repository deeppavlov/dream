FROM python:3.9.1

ARG SERVICE_PORT
ARG SERVICE_NAME

ENV SERVICE_PORT ${SERVICE_PORT}
ENV SERVICE_NAME ${SERVICE_NAME}

RUN mkdir /src
COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
COPY . /src/

WORKDIR /src

HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1
CMD gunicorn --workers=1 server:app -b 0.0.0.0:8122