FROM deeppavlov/base-gpu:0.12.1
RUN pip install --upgrade pip && pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.12.1

RUN apt-get update && apt-get install git -y

ARG SEQ_TAG_CONFIG
ARG EL_TAG_CONFIG
ARG CONFIG
ARG FINEGRAINED
ARG LOWERCASE
ARG PORT
ARG SRC_DIR
ARG SED_ARG=" | "

ENV SEQ_TAG_CONFIG=$SEQ_TAG_CONFIG
ENV EL_TAG_CONFIG=$EL_TAG_CONFIG
ENV CONFIG=$CONFIG
ENV FINEGRAINED=$FINEGRAINED
ENV LOWERCASE=$LOWERCASE
ENV PORT=$PORT

COPY ./annotators/entity_detection/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN python -m spacy download en_core_web_sm

COPY $SRC_DIR /src

WORKDIR /src
RUN python -m deeppavlov install $SEQ_TAG_CONFIG
RUN python -m deeppavlov install $EL_TAG_CONFIG

RUN sed -i "s|$SED_ARG|g" "$SEQ_TAG_CONFIG"
RUN sed -i "s|$SED_ARG|g" "$EL_TAG_CONFIG"

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:8103
