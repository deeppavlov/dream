FROM tensorflow/tensorflow:1.14.0-py3


########### DOWNLOADING MODELS ###########

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl &&\
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache

ARG DATA_URL=http://files.deeppavlov.ai/alexaprize_data/convert_reddit_v2.8.tar.gz

RUN mkdir -p /root/convert_data && \
    curl -L $DATA_URL --output /root/convert_data/convert_reddit_data.tar.gz && \
    cd /root/convert_data/ && \
    tar -xvf convert_reddit_data.tar.gz && \
    rm convert_reddit_data.tar.gz

########## MODELS ###########

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV MODEL_PATH /root/convert_data/convert
ENV DATABASE_PATH /root/convert_data/replies_v6.pkl
ENV CONFIDENCE_PATH /root/convert_data/confidences_v3.npy
ENV PYTHONPATH /usr/local/bin/python
ENV DEVICE cpu

COPY . .

CMD gunicorn --workers=2 server:app --timeout 120
