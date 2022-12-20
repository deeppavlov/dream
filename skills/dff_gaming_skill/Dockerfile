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

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

COPY skills/${SERVICE_NAME}/requirements.txt .
RUN pip install -r requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"

COPY skills/${SERVICE_NAME}/ ./
COPY ./common/ ./common/

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

COPY skills/${SERVICE_NAME}/data /data
WORKDIR /data
ENV BOOKREADS_DATA /data/bookreads_data.json
ENV IMDB_MOVIE_GENRES /data/imdb_movie_genres.json
ENV IGDB_GAME_GENRES /data/igdb_game_genres.json
ENV IGDB_GAME_THEMES /data/igdb_game_themes.json
ENV LINKTOS_BASED_ON_GAME_THEMES_AND_GENRES /data/linktos_based_on_game_themes_and_genres.json
ENV LINKTOS_SPECIAL /data/linktos_special.json
COPY skills/dff_book_skill/bookreads_data.json ${BOOKREADS_DATA}

ENV MINECRAFT_HOW_TOS /data/minecraft_how_tos.json

ENV GAMES_IGDB_SEARCH_RESULTS /data/games_igdb_search_results.json
ARG GAMES_IGDB_SEARCH_RESULTS_URL
RUN wget ${GAMES_IGDB_SEARCH_RESULTS_URL} -q -O ${GAMES_IGDB_SEARCH_RESULTS}
ENV GAMES_IGDB_IDS /data/games_igdb_ids.json
ARG GAMES_IGDB_IDS_URL
RUN wget ${GAMES_IGDB_IDS_URL} -q -O ${GAMES_IGDB_IDS}

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

WORKDIR /src
CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}
