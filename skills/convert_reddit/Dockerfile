FROM tensorflow/tensorflow:1.14.0-py3

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

ARG DATA_URL=http://files.deeppavlov.ai/alexaprize_data/convert_reddit_v2.3.punct.tar.gz

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV MODEL_PATH /root/convert_data/convert
ENV DATABASE_PATH /root/convert_data/replies_v2.pkl
ENV CONFIDENCE_PATH /root/convert_data/confidences_v3.npy
ENV PYTHONPATH /usr/local/bin/python
ENV DEVICE cpu

WORKDIR /app
RUN mkdir /root/convert_data/

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN wget $DATA_URL -q -P /root/convert_data/
RUN tar -xvzf /root/convert_data/*.tar.gz -C /root/convert_data/

COPY . .

CMD gunicorn --workers=2 server:app --timeout 120
