FROM python:3.9.16-slim
# ###################### IMMUTABLE SECTION ######################################
# Do not change anything in this section 
WORKDIR /src

COPY common/dff/requirements.txt common-reqs.txt
COPY skills/dff_knowledge_prompted_skill/requirements.txt .
RUN pip install --no-cache -r common-reqs.txt -r requirements.txt

RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# ###################### CUSTOM SECTION ######################################
# Here you can make changes 

COPY skills/dff_knowledge_prompted_skill/ ./
COPY ./common/ ./common/

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG PROMPT_FILE
ENV PROMPT_FILE ${PROMPT_FILE}
ARG GENERATIVE_SERVICE_URL
ENV GENERATIVE_SERVICE_URL ${GENERATIVE_SERVICE_URL}
ARG USER_KG_SERVICE_URL
ENV USER_KG_SERVICE_URL ${USER_KG_SERVICE_URL}
ARG GENERATIVE_TIMEOUT
ENV GENERATIVE_TIMEOUT ${GENERATIVE_TIMEOUT}
ARG GENERATIVE_SERVICE_CONFIG
ENV GENERATIVE_SERVICE_CONFIG ${GENERATIVE_SERVICE_CONFIG}
ARG N_UTTERANCES_CONTEXT
ENV N_UTTERANCES_CONTEXT ${N_UTTERANCES_CONTEXT}
ARG ENVVARS_TO_SEND
ENV ENVVARS_TO_SEND ${ENVVARS_TO_SEND}

ARG USE_KG_DATA
ENV USE_KG_DATA=$USE_KG_DATA

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --reload --timeout ${GENERATIVE_TIMEOUT:-30}
