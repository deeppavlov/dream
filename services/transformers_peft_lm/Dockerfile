FROM pytorch/pytorch:2.0.0-cuda11.7-cudnn8-devel

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG LANGUAGE=EN
ENV LANGUAGE ${LANGUAGE}

COPY ./services/transformers_peft_lm/requirements.txt /src/requirements.txt
RUN pip install --upgrade pip && pip install -r /src/requirements.txt

RUN apt-get update && apt-get install -y --allow-unauthenticated git wget
RUN pip install git+https://github.com/huggingface/transformers.git@15641892985b1d77acc74c9065c332cd7c3f7d7f
RUN pip install git+https://github.com/huggingface/peft.git@382b178911edff38c1ff619bbac2ba556bd2276b

RUN LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/
RUN pip install bitsandbytes

COPY services/transformers_peft_lm /src
COPY common /src/common

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
