FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

RUN python -m pip install --upgrade pip

RUN apt update
RUN apt install build-essential -y

RUN apt-get install ffmpeg -y
RUN apt-get update && apt-get install git -y

# RUN conda remove PyYAML
RUN mkdir /whisper_at 
RUN git clone https://github.com/YuanGongND/whisper-at.git /whisper_at 
RUN cd /whisper_at
RUN pwd

WORKDIR /whisper_at

RUN apt-get install wget -y

RUN wget https://www.dropbox.com/s/4vn2oatda321y7h/base_ori.pth?dl=1 -O /whisper_at/model.pth

COPY . /whisper_at

# HEALTHCHECK --interval=5s --timeout=90s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200