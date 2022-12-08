FROM python:3.9.1
# ###################### IMMUTABLE SECTION ######################################
# Do not change anything in this section 
WORKDIR /src

COPY common/dff/requirements.txt .
RUN pip install -r requirements.txt

# ###################### CUSTOM SECTION ######################################
# Here you can make changes

COPY annotators/user_knowledge_graph/requirements.txt .
RUN pip install -r requirements.txt
RUN python -m nltk.downloader wordnet
RUN pip install git+https://github.com/deeppavlov/custom_kg_svc

COPY annotators/user_knowledge_graph/ ./

ARG PORT
ENV PORT ${PORT}

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
#HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${PORT}/healthcheck || exit 1


CMD gunicorn --workers=1 server:app -b 0.0.0.0:${PORT}