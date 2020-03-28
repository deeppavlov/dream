FROM tensorflow/tensorflow:1.14.0-py3

########### DOWNLOADING MODELS ###########

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl &&\
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
	rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache

RUN mkdir -p /root/convert_data && \
    DATA_URL=http://files.deeppavlov.ai/alexaprize_data/convert_reddit_v2.3.tar.gz && \
    curl $DATA_URL > /root/convert_data/convert_reddit_data.tar.gz && \
    cd /root/convert_data/ && \
    tar -xvzf convert_reddit_data.tar.gz

########## MODELS ###########

RUN mkdir /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV MODEL_PATH /root/convert_data/convert
ENV DATABASE_PATH /root/convert_data/replies_v2.pkl
ENV CONFIDENCE_PATH /root/convert_data/confidences_v3.npy
ENV PYTHONPATH /usr/local/bin/python
ENV DEVICE cpu

COPY . /app/
WORKDIR /app

CMD gunicorn --workers=2 server:app --timeout 120
