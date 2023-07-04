FROM deeppavlov/deeppavlov:1.2.0-gpu

ARG CONFIG
ARG SERVICE_PORT
ARG SRC_DIR
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG
ENV SERVICE_PORT=$SERVICE_PORT

COPY ./annotators/NER_deeppavlov/requirements.txt /src/requirements.txt

COPY $SRC_DIR /src

WORKDIR /src

RUN pip install --upgrade pip && \
    pip install -r /src/requirements.txt

CMD gunicorn  --workers=1 --timeout 800 server:app -b 0.0.0.0:8021
