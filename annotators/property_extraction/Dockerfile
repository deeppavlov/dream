FROM deeppavlov/base-gpu:0.17.6

RUN apt-get update && apt-get install git -y

ARG CONFIG_T5
ARG CONFIG_REL_RANKER
ARG SRC_DIR
ARG SERVICE_PORT

ENV CONFIG_T5=$CONFIG_T5
ENV CONFIG_REL_RANKER=$CONFIG_REL_RANKER
ENV SERVICE_PORT=$SERVICE_PORT

COPY ./annotators/property_extraction/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY $SRC_DIR /src

WORKDIR /src

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:$SERVICE_PORT
