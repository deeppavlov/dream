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
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG PROMPT_FILE
ENV PROMPT_FILE ${PROMPT_FILE}
ARG GENERATIVE_SERVICE_URL
ENV GENERATIVE_SERVICE_URL ${GENERATIVE_SERVICE_URL}
ARG N_UTTERANCES_CONTEXT
ENV N_UTTERANCES_CONTEXT ${N_UTTERANCES_CONTEXT}

COPY skills/dff_template_prompted_skill/requirements.txt .
RUN pip install -r requirements.txt
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

COPY skills/dff_template_prompted_skill/ ./
COPY ./common/ ./common/

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}
