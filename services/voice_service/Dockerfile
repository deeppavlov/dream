# syntax=docker/dockerfile:experimental

FROM python:3.7

WORKDIR /src

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

ARG FLASK_APP
ENV FLASK_APP ${FLASK_APP}

RUN apt update
RUN apt install libsndfile1 -y
RUN apt install ffmpeg

RUN git clone https://github.com/moon-strider/audio-captioning-dcase /src/aux_files

RUN mkdir /src/aux_files/data/
RUN mkdir /src/aux_files/data/clotho_dataset/

RUN cp -r /src/aux_files/clotho-dataset/data/* /src/aux_files/data
RUN rm -f /src/aux_files/data/data_splits_features/.dummy
RUN mv /src/aux_files/wavetransformer/data/WT_pickles/* /src/aux_files/data/WT_pickles

COPY ./requirements.txt /src/requirements.txt
RUN cp /src/aux_files/wavetransformer/requirement_pip.txt /src/requirement_pip.txt
COPY ./ /src/

RUN pip install -r /src/requirements.txt
RUN pip install -r /src/requirement_pip.txt

RUN pwd
RUN ls -la
RUN ls -la /src
RUN echo 'port:'
RUN echo $SERVICE_PORT

# RUN flask --app server run -h 0.0.0.0 -p ${SERVICE_PORT}

#CMD tail -f /dev/null
CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200