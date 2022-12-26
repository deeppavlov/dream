FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

RUN python -m pip install --upgrade pip

RUN apt update
RUN apt install build-essential -y

RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get update && apt-get install git -y

RUN conda remove PyYAML

RUN mkdir /ofa && \
    git clone https://github.com/dariamitciuk/OFA.git /ofa && \
    cd /ofa && \
    pip install -r requirements.txt && \
    git checkout 153048138044edcbe0b099463810a971a7bf0057

WORKDIR /ofa

COPY ./requirements.txt /ofa/requirements.txt
RUN pip install -r requirements.txt

RUN apt-get install wget -y

RUN mkdir -p /opt/conda/lib/python3.7/site-packages/data/models

RUN wget http://files.deeppavlov.ai/dream_data/image_captioning/caption.pt -O /opt/conda/lib/python3.7/site-packages/data/models/caption.pt

COPY . /ofa

HEALTHCHECK --interval=5s --timeout=90s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200