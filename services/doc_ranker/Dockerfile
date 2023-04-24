# FROM deeppavlov/base-gpu:0.17.2
# RUN pip install --upgrade pip && pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.17.2
# RUN apt-key del 7fa2af80  && \
#     rm -f /etc/apt/sources.list.d/cuda*.list && \
#     wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-keyring_1.0-1_all.deb && \
#     dpkg -i cuda-keyring_1.0-1_all.deb
# RUN wget -O doc_ranker_config.json https://github.com/deepmipt/DeepPavlov/blob/0.1.6/deeppavlov/configs/odqa/en_odqa_infer_wiki.json
# RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*
FROM python:3.9.16
WORKDIR /src

ARG CONFIG_PATH
ENV CONFIG_PATH ${CONFIG_PATH}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG ORIGINAL_FILE_PATH
ENV ORIGINAL_FILE_PATH ${ORIGINAL_FILE_PATH}
ARG DATASET_PATH
ENV DATASET_PATH ${DATASET_PATH}

COPY services/doc_ranker/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"
RUN spacy download en_core_web_sm

COPY services/doc_ranker /src
COPY common /src/common

# RUN python -m deeppavlov download ${CONFIG_NAME}
RUN python train_model_if_not_exist.py

VOLUME ["/src/common"]

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=1200
