FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

ARG DATA_URL=http://files.deeppavlov.ai/alexaprize_data/midas.tar.gz

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

RUN mkdir /src
RUN mkdir /midas

RUN wget -q $DATA_URL -O /tmp/midas.tar.gz && tar -zvxf /tmp/midas.tar.gz -C /midas && rm -f /tmp/midas.tar.gz
COPY ./annotators/midas_classification/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
COPY ./annotators/midas_classification /src/

WORKDIR /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8090
