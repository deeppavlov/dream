FROM tensorflow/tensorflow:1.14.0-py3

ARG DATA_URL=http://files.deeppavlov.ai/alexaprize_data/convert_reddit_v2.3.punct.tar.gz

ADD $DATA_URL /root/convert_data/

RUN tar -xvzf /root/convert_data/*.tar.gz -C /root/convert_data/

RUN mkdir /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src/
WORKDIR /src

ENV MODEL_PATH /root/convert_data/convert
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV PYTHONPATH /usr/local/bin/python
ENV DEVICE cpu

CMD gunicorn --workers=2 server:app
