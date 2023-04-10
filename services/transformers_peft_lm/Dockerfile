FROM pytorch/pytorch:1.13.1-cuda11.6-cudnn8-runtime

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG HALF_PRECISION
ENV HALF_PRECISION ${HALF_PRECISION}

COPY ./services/transformers_lm/requirements.txt /src/requirements.txt
RUN pip install --upgrade pip && pip install -r /src/requirements.txt

RUN apt-get update && apt-get install -y --allow-unauthenticated git wget && rm -rf /var/lib/apt/lists/
RUN pip install git+https://github.com/huggingface/transformers.git@15641892985b1d77acc74c9065c332cd7c3f7d7f
RUN pip install git+https://github.com/huggingface/peft.git@382b178911edff38c1ff619bbac2ba556bd2276b

COPY services/transformers_lm /src
COPY common /src/common

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
