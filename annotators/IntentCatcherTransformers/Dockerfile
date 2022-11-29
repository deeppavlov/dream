FROM deeppavlov/base-gpu:0.17.2
RUN pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.17.2

RUN apt-key del 7fa2af80  && \
    rm -f /etc/apt/sources.list.d/cuda*.list && \
    wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-keyring_1.0-1_all.deb && \
    dpkg -i cuda-keyring_1.0-1_all.deb

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

WORKDIR /src

ARG CONFIG_NAME
ENV CONFIG_NAME ${CONFIG_NAME}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG INTENT_PHRASES_PATH
ENV INTENT_PHRASES_PATH ${INTENT_PHRASES_PATH}

COPY annotators/IntentCatcherTransformers/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./common/ ./common/
COPY annotators/IntentCatcherTransformers/ /src
WORKDIR /src

RUN python -m deeppavlov download ${CONFIG_NAME}
RUN python train_model_if_not_exist.py


CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
