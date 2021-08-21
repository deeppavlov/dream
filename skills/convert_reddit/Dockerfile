FROM tensorflow/tensorflow:1.14.0-py3

ARG DATA_URL=http://files.deeppavlov.ai/alexaprize_data/convert_reddit_v2.3.punct.tar.gz

ADD $DATA_URL /root/convert_data/

WORKDIR /app

RUN tar -xvzf /root/convert_data/*.tar.gz -C /root/convert_data/

COPY requirements.txt .
RUN pip install -r requirements.txt

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV MODEL_PATH /root/convert_data/convert
ENV DATABASE_PATH /root/convert_data/replies_v2.pkl
ENV CONFIDENCE_PATH /root/convert_data/confidences_v3.npy
ENV PYTHONPATH /usr/local/bin/python
ENV DEVICE cpu

COPY . .

CMD gunicorn --workers=2 server:app --timeout 120
