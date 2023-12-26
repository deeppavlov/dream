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

RUN gdown 'https://drive.google.com/uc?id=15rB8cn3MSJpFNIKHY3f9qvCMbgH2ZLmR' -O '/data/1d_cnn_with_opensmile.pt'
RUN gdown 'https://drive.google.com/uc?id=1ZHw2MEbjLwU5A7EaNysgVHZlaWq4FJZG' -O '/data/bert-large-uncased_none_seed-42.pt'
RUN gdown 'https://drive.google.com/uc?id=1XZVPI2ZvE0PbvhFMinsAp2z9SPPEsSjn' -O '/data/final_model.pt'
RUN gdown 'https://drive.google.com/uc?id=1DMUHqbwqn-j9XIhoqnfSwqyqrlPMkVJe' -O '/data/XCLIP_Augmented.pt'
RUN gdown 'https://drive.google.com/uc?id=1VxEQcso_Bsrzix1TykriJ2BLfUm9Gtx5' -O '/data/redundant_features.txt'

RUN echo $REDUNDANT_FEATURES