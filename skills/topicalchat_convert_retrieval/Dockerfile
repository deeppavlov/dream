FROM tensorflow/tensorflow:1.14.0-py3

########### DOWNLOADING MODELS ###########

RUN apt-get update && \
    apt-get install -qy --no-install-recommends \
        curl &&\
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache

RUN mkdir -p /root/convert_data && \
    DATA_URL=http://files.deeppavlov.ai/alexaprize_data/topicalchat_convert_candidates.tar.gz && \
    curl $DATA_URL > /root/convert_data/topicalchat_convert_candidates.tar.gz && \
    cd /root/convert_data/ && \
    tar -xvzf topicalchat_convert_candidates.tar.gz

########## MODELS ###########

RUN mkdir /src

COPY requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV MODEL_PATH /root/convert_data/convert
ENV DATABASE_PATH /root/convert_data/topicalchat_*_convert_candidates.pkl
ENV CONFIDENCE_PATH /root/convert_data/confidences.npy
ENV PYTHONPATH /usr/local/bin/python
ENV DEVICE cpu

COPY . /src/
WORKDIR /src

CMD gunicorn --workers=2 server:app --timeout 120
