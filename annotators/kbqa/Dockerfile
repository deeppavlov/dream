FROM deeppavlov/deeppavlov:1.2.0-gpu

ARG CONFIG
ARG COMMIT
ARG SERVICE_PORT
ARG SRC_DIR

ARG SED_ARG=" | "

ENV CONFIG=$CONFIG
ENV SERVICE_PORT=$SERVICE_PORT
ENV COMMIT=$COMMIT

COPY ./annotators/kbqa/requirements.txt /src/requirements.txt

RUN apt update &&  \
    apt install -y git

RUN pip install --upgrade pip && \
    pip install -r /src/requirements.txt && \
    pip install https://codeload.github.com/deeppavlov/DeepPavlov/tar.gz/${COMMIT}

COPY $SRC_DIR /src

WORKDIR /src

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

RUN python -m deeppavlov install $CONFIG && \
    python -m spacy download en_core_web_sm

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:8072
