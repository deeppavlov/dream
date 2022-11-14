# syntax=docker/dockerfile:experimental

FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

WORKDIR /src

ARG PRETRAINED_MODEL_FNAME
ENV PRETRAINED_MODEL_FNAME ${PRETRAINED_MODEL_FNAME}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG TOKENIZER_NAME_OR_PATH
ENV TOKENIZER_NAME_OR_PATH ${TOKENIZER_NAME_OR_PATH}

RUN mkdir /data/

RUN wget -c -q http://files.deeppavlov.ai/deeppavlov_data/${PRETRAINED_MODEL_FNAME} -P /data/

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src

RUN python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('${TOKENIZER_NAME_OR_PATH}');"
RUN python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('${TOKENIZER_NAME_OR_PATH}');"

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300

