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
RUN apt install ffmpeg -y
RUN python -m pip install -U pip
RUN pip install gdown

RUN git clone https://github.com/moon-strider/audio-captioning-dcase /src/aux_files
WORKDIR /src/aux_files
RUN git pull
WORKDIR /src

RUN pip install -e /src/aux_files/AudioCaption

RUN gdown https://drive.google.com/uc?id=11Gnme5XM-WcQ8C2vcbZ0m2ngmkvgGWwx -O /src/aux_files/AudioCaption/experiments.zip -c --no-check-certificate
RUN unzip /src/aux_files/AudioCaption/experiments.zip -d /src/aux_files/AudioCaption
RUN ls /src/aux_files/AudioCaption/experiments/clotho_v2
RUN ls /src/aux_files/AudioCaption/experiments/clotho_v2/train_val
RUN ls /src/aux_files/AudioCaption/experiments/clotho_v2/train_val/TransformerModel
RUN ls /src/aux_files/AudioCaption/experiments/clotho_v2/train_val/TransformerModel/cnn14rnn_trm
RUN ls /src/aux_files/AudioCaption/experiments/clotho_v2/train_val/TransformerModel/cnn14rnn_trm/seed_1
RUN rm /src/aux_files/AudioCaption/experiments.zip
RUN sed -i "s|sed/audioset_tagging_cnn/pretrained_weights/Cnn14_mAP=0.431.pth|/src/aux_files/pretrained_weights/model.pth|" /src/aux_files/AudioCaption/experiments/clotho_v2/train_val/TransformerModel/cnn14rnn_trm/seed_1/config.yaml
RUN sed -i "s|/home/ilia/projects/audio-captioning/pretrained_weights/Cnn14_mAP=0.431.pth|/src/aux_files/pretrained_weights/model.pth|" /src/aux_files/AudioCaption/experiments/clotho_v2/train_val/TransformerModel/cnn14rnn_trm/seed_1/config.yaml
RUN cat /src/aux_files/AudioCaption/experiments/clotho_v2/train_val/TransformerModel/cnn14rnn_trm/seed_1/config.yaml
# PATH
RUN mkdir /src/aux_files/pretrained_weights
RUN gdown https://drive.google.com/uc?id=1CVD_JFEx9iFg8DH1cZd81gcPvxrb8uZq -O /src/aux_files/pretrained_weights/model.pth -c --no-check-certificate

# SWA
# RUN gdown https://drive.google.com/file/d/1V9eHT4s8VbiJwxRyz8Xnu7L6yHzj3aTi/view?usp=share_link -O /src/aux_files/AudioCaption/experiments/clotho_v2/train_val/TransformerModel/cnn14rnn_trm/seed_1/swa.pth

COPY ./requirements.txt /src/requirements.txt
COPY ./ /src/

RUN pip install -r /src/requirements.txt
RUN pip install -r /src/aux_files/reqs.txt

RUN pwd
RUN ls -la
RUN ls -la /src
RUN echo 'port:'
RUN echo $SERVICE_PORT

# RUN flask --app server run -h 0.0.0.0 -p ${SERVICE_PORT}

#CMD tail -f /dev/null