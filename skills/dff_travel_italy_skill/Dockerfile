FROM python:3.9.1
# ###################### IMMUTABLE SECTION ######################################
# Do not change anything in this section 
WORKDIR /src

COPY common/dff/requirements.txt .
RUN pip install -r requirements.txt

# ###################### CUSTOM SECTION ######################################
# Here you can make changes 

ARG SERVICE_NAME
ARG TERMINUSDB_SERVER_PASSWORD
ARG TERMINUSDB_SERVER_URL
ARG TERMINUSDB_SERVER_TEAM
ARG TERMINUSDB_SERVER_DB

ENV SERVICE_NAME ${SERVICE_NAME}
ENV TERMINUSDB_SERVER_PASSWORD=$TERMINUSDB_SERVER_PASSWORD
ENV TERMINUSDB_SERVER_URL=$TERMINUSDB_SERVER_URL
ENV TERMINUSDB_SERVER_TEAM=$TERMINUSDB_SERVER_TEAM
ENV TERMINUSDB_SERVER_DB=$TERMINUSDB_SERVER_DB

COPY skills/${SERVICE_NAME}/requirements.txt .
RUN pip install -r requirements.txt && \
    python -m nltk.downloader wordnet

COPY skills/${SERVICE_NAME}/ ./
COPY ./common/ ./common/

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1


CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}
