FROM deeppavlov/deeppavlov:1.2.0

ARG MODEL_CKPT

ENV MODEL_CKPT ${MODEL_CKPT}

ARG DATA_ARG
ARG MODEL1_ARG
ARG MODEL2_ARG

WORKDIR /src
COPY . /src

RUN apt-get update && \
    apt-get install -y --allow-unauthenticated git wget && \
    rm -rf /var/lib/apt/lists/* && \
    pip install -r /src/requirements.txt &&\
    python -c "import nltk; nltk.download('punkt')" && \
    mkdir -p /opt/conda/lib/python3.7/site-packages/data/models &&\
    wget $DATA_ARG -q -P /opt/conda/lib/python3.7/site-packages/data &&\
    tar -xvzf /opt/conda/lib/python3.7/site-packages/data/*.tar.gz -C /opt/conda/lib/python3.7/site-packages/data &&\
    rm /opt/conda/lib/python3.7/site-packages/data/*.tar.gz &&\
    wget $MODEL1_ARG -q -P /opt/conda/lib/python3.7/site-packages/data/models &&\
    tar -xvzf /opt/conda/lib/python3.7/site-packages/data/models/*.tar.gz -C /opt/conda/lib/python3.7/site-packages/data/models &&\
    rm /opt/conda/lib/python3.7/site-packages/data/models/*.tar.gz &&\
    wget $MODEL2_ARG -q -P /opt/conda/lib/python3.7/site-packages/data/models &&\
    tar -xvzf /opt/conda/lib/python3.7/site-packages/data/models/*.tar.gz -C /opt/conda/lib/python3.7/site-packages/data/models &&\
    rm /opt/conda/lib/python3.7/site-packages/data/models/*.tar.gz

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8083
