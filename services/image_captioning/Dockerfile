FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

RUN python -m pip install --upgrade pip

RUN apt update
RUN apt install build-essential -y
RUN apt-get update && apt-get install git -y
RUN apt-get install ffmpeg libsm6 libxext6  -y

RUN conda remove PyYAML

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN git clone https://github.com/OFA-Sys/OFA && \
    cd OFA && \
    git checkout c8313b9e8e4cf4f4df693e96848d337ed74ab68d && \
    pip install -r requirements.txt

RUN apt-get install wget -y
RUN pip install gdown

RUN mkdir -p /opt/conda/lib/python3.7/site-packages/data/models

RUN gdown 1WBQl0WlzvdctslJyLNgedYpRrWAZC69X -O /opt/conda/lib/python3.7/site-packages/data/models/caption.pt

COPY . /src

HEALTHCHECK --interval=5s --timeout=90s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
