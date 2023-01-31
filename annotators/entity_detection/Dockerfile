FROM deeppavlov/base-gpu:0.12.1

RUN apt-get update && apt-get install git -y

ARG SEQ_TAG_CONFIG
ARG CONFIG
ARG FINEGRAINED
ARG LOWERCASE
ARG PORT
ARG SRC_DIR

ENV SEQ_TAG_CONFIG=$SEQ_TAG_CONFIG
ENV CONFIG=$CONFIG
ENV FINEGRAINED=$FINEGRAINED
ENV LOWERCASE=$LOWERCASE
ENV PORT=$PORT

COPY ./annotators/entity_detection/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN pip install pyopenssl==23.0.0 && python -m spacy download en_core_web_sm

COPY $SRC_DIR /src

WORKDIR /src

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:$PORT
