FROM deeppavlov/base-gpu:0.17.6

RUN apt-get update && apt-get install git -y

ARG SEQ_TAG_CONFIG
ARG CONFIG
ARG FINEGRAINED
ARG SERVICE_PORT
ARG SRC_DIR

ENV SEQ_TAG_CONFIG=$SEQ_TAG_CONFIG
ENV CONFIG=$CONFIG
ENV FINEGRAINED=$FINEGRAINED
ENV SERVICE_PORT=$SERVICE_PORT

COPY ./annotators/entity_detection/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN pip install pyopenssl==23.0.0 && python -m spacy download en_core_web_sm

COPY $SRC_DIR /src

WORKDIR /src
RUN python -m deeppavlov install $SEQ_TAG_CONFIG

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:$SERVICE_PORT
