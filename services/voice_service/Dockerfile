FROM python:3.7

# Set the working directory
WORKDIR /src

# Set environment variables for service
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

RUN python -m pip install --upgrade pip

COPY ./requirements.txt /src/requirements.txt
COPY ./server.py /src/server.py

RUN mkdir -p /src/aux_files/AudioCaption/
RUN wget --no-check-certificate -O /src/aux_files/AudioCaption/experiments.zip https://files.deeppavlov.ai/dolidze/for_voice_service/AudioCaption.zip
RUN unzip /src/aux_files/AudioCaption/experiments.zip -d /src
RUN ls /src

RUN apt update
RUN apt install -y gcc libsndfile1-dev ffmpeg

RUN python -m pip install -r requirements.txt
RUN pip install -r /src/AudioCaption/requirements.txt

RUN python -m pip install numba==0.48
RUN python -m pip install resampy==0.3.1
RUN python -m pip install torchaudio==0.9.1
RUN python -m pip install torchlibrosa==0.0.9
RUN pip install sndfile

# Create directory for pretrained models and download them
RUN mkdir -p pretrained_feature_extractors
RUN wget https://github.com/wsntxxn/AudioCaption/releases/download/v0.0.2/contrastive_pretrain_cnn14_bertm.pth -O pretrained_feature_extractors/contrastive_pretrain_cnn14_bertm.pth
RUN wget https://github.com/wsntxxn/AudioCaption/releases/download/v0.0.2/audiocaps_cntrstv_cnn14rnn_trm.zip -O audiocaps_cntrstv_cnn14rnn_trm.zip
RUN unzip audiocaps_cntrstv_cnn14rnn_trm.zip -d pretrained_feature_extractors

RUN pip install -e /src/AudioCaption