FROM nvidia/cuda:12.1.1-base-ubuntu20.04

RUN apt update
RUN apt install -y python3.9
RUN apt install -y git python3-pip

ARG VIDEO_PRETRAINED
ARG TEXT_PRETRAINED
ARG MODEL_PATH
ARG MULTIMODAL_MODEL
ARG REDUNDANT_FEATURES

ENV VIDEO_PRETRAINED=$VIDEO_PRETRAINED
ENV TEXT_PRETRAINED=$TEXT_PRETRAINED
ENV MULTIMODAL_MODEL=$MULTIMODAL_MODEL
ENV MODEL_PATH=$MODEL_PATH
ENV REDUNDANT_FEATURES=$REDUNDANT_FEATURES

WORKDIR /src

COPY . /src
RUN mkdir /data
RUN pip install -r requirements.txt

RUN apt install -y ffmpeg=7:4.2.7-0ubuntu0.1 libsm6=2:1.2.3-1 libxext6=2:1.3.4-0ubuntu1

RUN pip install gdown==4.7.1

RUN git clone https://github.com/anna-a-m/MultimodalERC /data/repo && cd /data/repo && git reset --hard 84097d442b23b5a9238b5090a04e2625741314ae

RUN mv -f /data/repo/* /data/ && rm -rf /data/repo

RUN touch /data/multimodal_concat/__init__.py

RUN apt-get install -y wget

RUN wget -O models http://files.deeppavlov.ai/dream_data/emotion_detection/emotion_detection_v1.tar.gz && tar -xf models -C /data/
RUN wget -O redundant_feat http://files.deeppavlov.ai/dream_data/emotion_detection/redundant_feat.txt && mv -f redundant_feat /data/