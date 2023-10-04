FROM deeppavlov/deeppavlov:1.2.0-gpu

RUN apt-get update && apt-get install git -y

ARG CONFIG
ARG CONFIG_WIKI
ARG CONFIG_WHOW
ARG SERVICE_PORT
ARG SRC_DIR
ARG SED_ARG=" | "
ARG N_FACTS

ENV CONFIG=$CONFIG
ENV CONFIG_WIKI=$CONFIG_WIKI
ENV CONFIG_WHOW=$CONFIG_WHOW
ENV SERVICE_PORT=$SERVICE_PORT
ENV N_FACTS=$N_FACTS

COPY ./annotators/fact_retrieval/requirements.txt /src/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /src/requirements.txt

COPY $SRC_DIR /src

WORKDIR /src
COPY ./common/ ./common/

RUN sed -i "s|$SED_ARG|g" "$CONFIG" && \
    sed -i "s|$SED_ARG|g" "$CONFIG_WIKI" && \
    sed -i "s|$SED_ARG|g" "$CONFIG_WHOW"

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:8100
