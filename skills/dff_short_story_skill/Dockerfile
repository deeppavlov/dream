FROM python:3.9.1
# ###################### IMMUTABLE SECTION ######################################
# Do not change anything in this section 
WORKDIR /src

COPY common/dff/requirements.txt .
RUN pip install -r requirements.txt

# ###################### CUSTOM SECTION ######################################
# Here you can make changes 

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

COPY skills/${SERVICE_NAME}/requirements.txt .
RUN pip install -r requirements.txt
RUN python -m nltk.downloader wordnet

COPY skills/${SERVICE_NAME}/ ./
COPY ./common/ ./common/

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

ARG STORY_TYPE
ENV STORY_TYPE ${STORY_TYPE}
ARG PROMPT_STORYGPT_SERVICE_URL
ENV PROMPT_STORYGPT_SERVICE_URL ${PROMPT_STORYGPT_SERVICE_URL}
ARG STORYGPT_SERVICE_URL
ENV STORYGPT_SERVICE_URL ${STORYGPT_SERVICE_URL}

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
# HEALTHCHECK --interval=500s --timeout=300s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1


CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=3
