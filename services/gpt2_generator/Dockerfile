FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

WORKDIR /src

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG CONFIG_NAME
ENV CONFIG_NAME ${CONFIG_NAME}
ARG N_HYPOTHESES_TO_GENERATE=3
ENV N_HYPOTHESES_TO_GENERATE ${N_HYPOTHESES_TO_GENERATE}
ARG MAX_HISTORY_DEPTH=3
ENV MAX_HISTORY_DEPTH ${MAX_HISTORY_DEPTH}


COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN python -c "from transformers import GPT2Tokenizer; GPT2Tokenizer.from_pretrained('${PRETRAINED_MODEL_NAME_OR_PATH}');"
RUN python -c "from transformers import GPT2LMHeadModel; GPT2LMHeadModel.from_pretrained('${PRETRAINED_MODEL_NAME_OR_PATH}');"

COPY . /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
