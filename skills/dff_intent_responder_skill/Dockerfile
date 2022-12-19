FROM python:3.9.1
# ###################### IMMUTABLE SECTION ######################################
# Do not change anything in this section 
WORKDIR /src

COPY common/dff/requirements.txt .
RUN pip install -r requirements.txt

# ###################### CUSTOM SECTION ######################################
# Here you can make changes 

ARG LANGUAGE=EN
ENV LANGUAGE ${LANGUAGE}

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

ARG INTENT_RESPONSE_PHRASES_FNAME
ENV INTENT_RESPONSE_PHRASES_FNAME ${INTENT_RESPONSE_PHRASES_FNAME}

COPY skills/${SERVICE_NAME}/requirements.txt .
RUN pip install -r requirements.txt
RUN python -m nltk.downloader wordnet

COPY skills/${SERVICE_NAME}/ ./
COPY ./common/ ./common/

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

ARG ROS_FSM_SERVER
ENV ROS_FSM_SERVER ${ROS_FSM_SERVER}

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1


CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}
