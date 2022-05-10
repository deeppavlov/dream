FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

RUN python -m pip install --upgrade pip

RUN apt update
RUN apt install build-essential -y
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

RUN conda remove PyYAML

COPY ./ofa /src/ofa
RUN sed '1d' /src/ofa/requirements.txt | xargs -I {} pip install {}

COPY ./fairseq /src/fairseq
RUN pip install --use-feature=in-tree-build /src/fairseq

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN apt-get install wget -y

COPY . /src

RUN mkdir /src/ofa/checkpoints
RUN wget https://ofa-silicon.oss-us-west-1.aliyuncs.com/checkpoints/caption_large_best_clean.pt -O /src/ofa/checkpoints/caption.pt


HEALTHCHECK --interval=5s --timeout=90s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
