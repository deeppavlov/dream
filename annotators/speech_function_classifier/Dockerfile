FROM pytorch/pytorch:1.9.0-cuda10.2-cudnn7-runtime

WORKDIR /src

RUN apt-get update && apt-get install -y --allow-unauthenticated git curl && rm -rf /var/lib/apt/lists/*

# RUN git clone -b feat/speech-fn https://github.com/deeppavlov/DeepPavlov.git && \
# 	cd DeepPavlov && pip install -e . && cd .. && rm -rf DeepPavlov && python -m deeppavlov download speech_fn

RUN pip install git+https://github.com/deeppavlov/DeepPavlov.git@e2ae2d91edad414736d15520eb1820cb6c06565d && \
        python -m deeppavlov download speech_fn

COPY . ./

RUN pip install -r requirements.txt

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}