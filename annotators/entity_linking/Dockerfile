FROM tensorflow/tensorflow:1.15.2-gpu

RUN apt-get -y update && \
    apt-get install -y software-properties-common && \
    apt-get update && apt-get install git -y

ARG CONFIG
ARG COMMIT=0.13.0
ARG PORT
ARG SRC_DIR
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG
ENV PORT=$PORT

COPY ./annotators/entity_linking/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN pip install git+https://github.com/deepmipt/DeepPavlov.git@${COMMIT}

COPY $SRC_DIR /src

WORKDIR /src

RUN python -m deeppavlov install $CONFIG

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:8075
