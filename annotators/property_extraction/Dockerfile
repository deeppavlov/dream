FROM deeppavlov/base-gpu:0.17.6

RUN apt-get update && apt-get install git -y

ARG CONFIG
ARG SRC_DIR

ENV CONFIG=$CONFIG

COPY ./annotators/property_extraction/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY $SRC_DIR /src

WORKDIR /src

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:8136
