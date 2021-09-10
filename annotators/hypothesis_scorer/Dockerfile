FROM tensorflow/tensorflow:1.15.2-gpu

ARG MIDAS_DATA_URL=http://files.deeppavlov.ai/alexaprize_data/midas.tar.gz
ARG CONVERT_DATA_URL=http://files.deeppavlov.ai/alexaprize_data/convert_reddit_v2.8.tar.gz

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

RUN mkdir /src
RUN mkdir /midas
RUN mkdir /convert

RUN wget -q $MIDAS_DATA_URL -O /tmp/midas.tar.gz && tar -zvxf /tmp/midas.tar.gz -C /midas && rm -f /tmp/midas.tar.gz
RUN wget -q $CONVERT_DATA_URL -O /tmp/convert.tar.gz && tar -zvxf /tmp/convert.tar.gz -C /convert && rm -f /tmp/convert.tar.gz

COPY ./requirements.txt /src/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /src/requirements.txt
RUN pip uninstall -y protobuf tensorflow tensorflow-gpu && \
    pip install --upgrade --force-reinstall tensorflow-gpu==1.14.0

COPY . /src/

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

WORKDIR /src

CMD uvicorn server:app --reload --host 0.0.0.0 --port ${SERVICE_PORT}
