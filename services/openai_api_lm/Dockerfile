FROM python:3.7.4

WORKDIR /src

COPY ./services/openai_api_lm/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

ARG PRETRAINED_MODEL_NAME_OR_PATH
ENV PRETRAINED_MODEL_NAME_OR_PATH ${PRETRAINED_MODEL_NAME_OR_PATH}

COPY . /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
