FROM nvidia/cuda:12.1.1-base-ubuntu20.04

RUN apt update
RUN apt install -y python3.9
RUN apt install -y git python3-pip

ARG VIDEO_PRETRAINED
ARG TEXT_PRETRAINED
ARG MODEL_PATH
ARG MULTIMODAL_MODEL

ENV VIDEO_PRETRAINED=$VIDEO_PRETRAINED
ENV TEXT_PRETRAINED=$TEXT_PRETRAINED
ENV MULTIMODAL_MODEL=$MULTIMODAL_MODEL
ENV MODEL_PATH=$MODEL_PATH

WORKDIR /src

COPY . /src
RUN mkdir /data
RUN pip install -r requirements.txt

RUN apt install -y ffmpeg=7:4.2.7-0ubuntu0.1 libsm6=2:1.2.3-1 libxext6=2:1.3.4-0ubuntu1

RUN pip install gdown==4.7.1

RUN git clone https://github.com/anna-a-m/MultimodalERC /data/repo && cd /data/repo && git reset --hard 95cbd971ecb2a057f0162f0384bba28c6fddee31

RUN mv -f /data/repo/* /data/ && rm -rf /data/repo

RUN touch /data/multimodal_concat/__init__.py

RUN gdown 'https://drive.google.com/uc?id=12C36rGUe7tuWGAh_FByw80c3wAtdUHx8' -O '/data/1d_cnn_with_opensmile.pt'
RUN gdown 'https://drive.google.com/uc?id=1ZHw2MEbjLwU5A7EaNysgVHZlaWq4FJZG' -O '/data/bert-large-uncased_none_seed-42.pt'
RUN gdown 'https://drive.google.com/uc?id=1tDf-jWihZ6M0oX-niOfVmLUimJqYrG_M' -O '/data/final_model.pt'
RUN gdown 'https://drive.google.com/uc?id=1DMUHqbwqn-j9XIhoqnfSwqyqrlPMkVJe' -O '/data/XCLIP_Augmented.pt'