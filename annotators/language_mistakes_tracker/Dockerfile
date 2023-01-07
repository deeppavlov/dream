FROM python:3.9.1

ARG SRC_DIR

WORKDIR /src

COPY $SRC_DIR/requirements.txt .
RUN pip install -r requirements.txt

COPY $SRC_DIR .
COPY ./common/ ./common/
COPY ./skills/dff_language_practice_skill/data ./data

ARG SERVICE_PORT
ARG SERVICE_NAME

ENV SERVICE_PORT ${SERVICE_PORT}
ENV SERVICE_NAME ${SERVICE_NAME}

HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1
CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}