FROM deeppavlov/base-gpu:1.0.0rc1

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
