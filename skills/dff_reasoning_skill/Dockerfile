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
ARG API_CONFIGS
ENV API_CONFIGS ${API_CONFIGS}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG GENERATIVE_TIMEOUT
ENV GENERATIVE_TIMEOUT ${GENERATIVE_TIMEOUT}
ARG N_UTTERANCES_CONTEXT
ENV N_UTTERANCES_CONTEXT ${N_UTTERANCES_CONTEXT}
ARG GENERATIVE_SERVICE_URL
ENV GENERATIVE_SERVICE_URL ${GENERATIVE_SERVICE_URL}
ARG GENERATIVE_SERVICE_CONFIG
ENV GENERATIVE_SERVICE_CONFIG ${GENERATIVE_SERVICE_CONFIG}
ARG ENVVARS_TO_SEND
ENV ENVVARS_TO_SEND ${ENVVARS_TO_SEND}


COPY skills/dff_reasoning_skill/requirements.txt .
RUN pip install -r requirements.txt

COPY skills/dff_reasoning_skill/ ./
COPY ./common/ ./common/
COPY ./skills/dff_weather_skill/tools/ ./tools/
COPY ./skills/dff_weather_skill/data/ ./data/


CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}
