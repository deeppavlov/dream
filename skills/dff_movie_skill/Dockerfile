FROM python:3.9.1


# ###################### IMMUTABLE SECTION ######################################
# Do not change anything in this section 
WORKDIR /src

COPY common/dialogflow_framework/requirements.txt .
RUN pip install -r requirements.txt

COPY common/dialogflow_framework/scripts /scripts

RUN bash /scripts/programy_logger_off.sh

# ###################### CUSTOM SECTION ######################################
# Here you can make changes 

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

COPY skills/${SERVICE_NAME}/requirements.txt .
RUN pip install -r requirements.txt

RUN python -c "import nltk; nltk.download('punkt')"

ARG DATABASE_URL
ARG MOVIE_PLOTS_URL

WORKDIR /data
RUN wget ${DATABASE_URL} -q -O /data/database_most_popular_main_info.json
RUN wget  $MOVIE_PLOTS_URL -q -P /data/
RUN tar -xvzf /data/*.tar.gz -C /data/
WORKDIR /src

COPY skills/${SERVICE_NAME}/ ./
RUN cd databases && wget https://files.deeppavlov.ai/dream/dff_movie_skill/w2_.txt
COPY ./common/ ./common/

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1


CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}
