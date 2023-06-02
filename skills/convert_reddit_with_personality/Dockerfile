FROM tensorflow/tensorflow:1.14.0-py3

########### DOWNLOADING MODELS ###########

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl &&\
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
	rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache

RUN mkdir -p /root/convert_data && \
    DATA_URL=http://files.deeppavlov.ai/alexaprize_data/convert_reddit.tar.gz && \
    curl $DATA_URL > /root/convert_data/convert_reddit.tar.gz && \
    cd /root/convert_data/ && \
    tar -xvzf convert_reddit.tar.gz

########## MODELS ###########

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV MODEL_PATH /root/convert_data/convert
ENV DATABASE_PATH /root/convert_data/replies.pkl
ENV CONFIDENCE_PATH /root/convert_data/confidences.npy
ENV PYTHONPATH /usr/local/bin/python
ENV DEVICE cpu

COPY . /app/

CMD gunicorn --workers=2 server:app --timeout 120
