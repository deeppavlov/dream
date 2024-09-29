# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

WORKDIR /src

ARG PRETRAINED_MODEL_FNAME
ENV PRETRAINED_MODEL_FNAME ${PRETRAINED_MODEL_FNAME}
ARG CONFIG_NAME
ENV CONFIG_NAME ${CONFIG_NAME}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG RET_SCALE_FACTOR
ENV RET_SCALE_FACTOR ${RET_SCALE_FACTOR}

RUN python -m pip install --upgrade pip
RUN apt-get update && apt-get install -y wget

ENV PYTHONPATH "/src/fromage:/fromage:$PYTHONPATH"

COPY ./services/fromage/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN apt-get update && apt-get install git -y

RUN mkdir /fromage && \
    git clone https://github.com/ciwwwnd/fromage.git /fromage

RUN mkdir -p /services/fromage/fromage_model
RUN wget --no-check-certificate -O /services/fromage/fromage_model/cc3m_embeddings.pkl https://files.deeppavlov.ai/dolidze/for_fromage/cc3m_embeddings.pkl 
RUN wget --no-check-certificate -O /services/fromage/fromage_model/model_args.json https://files.deeppavlov.ai/dolidze/for_fromage/model_args.json
RUN wget --no-check-certificate -O /services/fromage/fromage_model/pretrained_ckpt.pth.tar https://files.deeppavlov.ai/dolidze/for_fromage/pretrained_ckpt.pth.tar

COPY ./services/fromage/ /src/
COPY ./common/ ./common/

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200
