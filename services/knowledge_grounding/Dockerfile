FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

ARG MODEL_CKPT
ENV MODEL_CKPT ${MODEL_CKPT}

ARG DATA_ARG
ARG MODEL1_ARG
ARG MODEL2_ARG

RUN apt-get update && apt-get install -y --allow-unauthenticated git wget && rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"

# install parlai
RUN pip install git+https://github.com/Saraharas/ParlAI@v0.9.4-kg-batch-2models#egg=ParlAI

# create dirs for data and models
RUN mkdir -p /opt/conda/lib/python3.7/site-packages/data/models

#load data
RUN wget $DATA_ARG -q -P /opt/conda/lib/python3.7/site-packages/data &&\
tar -xvzf /opt/conda/lib/python3.7/site-packages/data/*.tar.gz -C /opt/conda/lib/python3.7/site-packages/data &&\
rm /opt/conda/lib/python3.7/site-packages/data/*.tar.gz

# load models tar.gz
RUN wget $MODEL1_ARG -q -P /opt/conda/lib/python3.7/site-packages/data/models &&\
tar -xvzf /opt/conda/lib/python3.7/site-packages/data/models/*.tar.gz -C /opt/conda/lib/python3.7/site-packages/data/models &&\
rm /opt/conda/lib/python3.7/site-packages/data/models/*.tar.gz

RUN wget $MODEL2_ARG -q -P /opt/conda/lib/python3.7/site-packages/data/models &&\
tar -xvzf /opt/conda/lib/python3.7/site-packages/data/models/*.tar.gz -C /opt/conda/lib/python3.7/site-packages/data/models &&\
rm /opt/conda/lib/python3.7/site-packages/data/models/*.tar.gz

WORKDIR /src

COPY . /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8083
