FROM deeppavlov/base-gpu:0.17.5

RUN pip install git+https://github.com/deeppavlov/DeepPavlov.git@1.3.0

WORKDIR /base/DeepPavlov

WORKDIR /src
RUN mkdir common

COPY annotators/dnnc_intents/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

RUN python -m spacy download en_core_web_sm

ARG SERVICE_PORT
ENV SERVICE_PORT=$SERVICE_PORT
ARG CONFIG
ENV CONFIG=$CONFIG
ARG CLASSES
ENV CLASSES=$CLASSES

COPY annotators/dnnc_intents/ ./
COPY common/ common/

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200 --preload
