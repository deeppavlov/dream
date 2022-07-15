FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

ARG SERVICE_PORT
ENV SERVICE_PORT=$SERVICE_PORT
ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}

WORKDIR /src
RUN mkdir common

COPY annotators/sentence_ranker/requirements.txt .
RUN pip install -r requirements.txt

RUN python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('${PRETRAINED_MODEL_NAME_OR_PATH}');"
RUN python -c "from transformers import AutoModel; AutoModel.from_pretrained('${PRETRAINED_MODEL_NAME_OR_PATH}');"

COPY . /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
