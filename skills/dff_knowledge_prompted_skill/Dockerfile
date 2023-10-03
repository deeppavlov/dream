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
ARG SERVICE_PORT
ARG PROMPT_FILE
ARG GENERATIVE_SERVICE_URL
ARG GENERATIVE_TIMEOUT
ARG GENERATIVE_SERVICE_CONFIG
ARG N_UTTERANCES_CONTEXT
ARG ENVVARS_TO_SEND
ARG USE_BOT_KG_DATA


ENV SERVICE_NAME=$SERVICE_NAME
ENV SERVICE_PORT=$SERVICE_PORT
ENV PROMPT_FILE=$PROMPT_FILE
ENV GENERATIVE_SERVICE_URL=$GENERATIVE_SERVICE_URL
ENV GENERATIVE_TIMEOUT=$GENERATIVE_TIMEOUT
ENV GENERATIVE_SERVICE_CONFIG=$GENERATIVE_SERVICE_CONFIG
ENV N_UTTERANCES_CONTEXT=$N_UTTERANCES_CONTEXT
ENV ENVVARS_TO_SEND=$ENVVARS_TO_SEND
ENV USE_BOT_KG_DATA=$USE_BOT_KG_DATA


ARG ALLOW_PROMPT_RESET=0
ENV ALLOW_PROMPT_RESET=$ALLOW_PROMPT_RESET

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --reload --timeout ${GENERATIVE_TIMEOUT:-30}
