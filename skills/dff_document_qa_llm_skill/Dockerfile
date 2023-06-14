FROM python:3.9.1
# ###################### IMMUTABLE SECTION ######################################
# Do not change anything in this section 
WORKDIR /src

COPY common/dff/requirements.txt .
RUN pip install -r requirements.txt

# ###################### CUSTOM SECTION ######################################
# Here you can make changes 

COPY skills/dff_document_qa_llm_skill/requirements.txt .
RUN pip install -r requirements.txt && python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
RUN mkdir /data/

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG GENERATIVE_TIMEOUT
ENV GENERATIVE_TIMEOUT ${GENERATIVE_TIMEOUT}
ARG GENERATIVE_SERVICE_URL
ENV GENERATIVE_SERVICE_URL ${GENERATIVE_SERVICE_URL}
ARG GENERATIVE_SERVICE_CONFIG
ENV GENERATIVE_SERVICE_CONFIG ${GENERATIVE_SERVICE_CONFIG}
ARG ENVVARS_TO_SEND
ENV ENVVARS_TO_SEND ${ENVVARS_TO_SEND}
ARG N_UTTERANCES_CONTEXT
ENV N_UTTERANCES_CONTEXT ${N_UTTERANCES_CONTEXT}

COPY skills/dff_document_qa_llm_skill/ /src
COPY documents /src/documents
COPY common /src/common

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --reload --timeout ${GENERATIVE_TIMEOUT:-30}
