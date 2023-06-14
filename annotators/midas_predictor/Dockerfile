FROM python:3.9.16-slim

COPY ./requirements.txt /src/requirements.txt

RUN pip install -r /src/requirements.txt

COPY ./ /src/
COPY ./common/ /src/common/
WORKDIR /src

RUN mkdir /data/

ARG SERVICE_NAME
ARG SERVICE_PORT

ENV SERVICE_NAME ${SERVICE_NAME}
ENV SERVICE_PORT ${SERVICE_PORT}

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8121
