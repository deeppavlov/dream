FROM deeppavlov/deeppavlov:1.2.0-gpu

WORKDIR /base/DeepPavlov

WORKDIR /src
RUN mkdir common

COPY annotators/dnnc_intents/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

ARG SERVICE_PORT
ENV SERVICE_PORT=$SERVICE_PORT
ARG CONFIG
ENV CONFIG=$CONFIG

COPY annotators/dnnc_intents/ ./
COPY common/ common/

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200 --preload
