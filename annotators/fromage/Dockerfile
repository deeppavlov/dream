# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

WORKDIR /src

ARG PRETRAINED_MODEL_FNAME
ENV PRETRAINED_MODEL_FNAME ${PRETRAINED_MODEL_FNAME}
ARG CONFIG_NAME
ENV CONFIG_NAME ${CONFIG_NAME}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

COPY ./annotators/fromage/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN apt-get update && apt-get install git -y
RUN pip install gdown

RUN mkdir /fromage && \
    git clone https://github.com/ciwwwnd/fromage.git /fromage && \
    cd /fromage 

RUN mkdir -p /annotators/fromage/fromage_model
RUN gdown 1wMojZNqEwApNlsCZVvSgQVtZLgbeLoKi -O /annotators/fromage/fromage_model/cc3m_embeddings.pkl
RUN gdown 1qyDiUw6uMA4nijLaNpr3J-2pigdIANYE -O /annotators/fromage/fromage_model/model_args.json
RUN gdown 1oG_fWDje3M6XBoU2GtrOlrqaffJEhxyN -O /annotators/fromage/fromage_model/pretrained_ckpt.pth.tar

COPY ./annotators/fromage/ /src/
COPY ./common/ ./common/
WORKDIR /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=5000
