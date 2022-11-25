FROM tensorflow/tensorflow:1.15.2-gpu

RUN apt-key del 7fa2af80  && \
    rm -f /etc/apt/sources.list.d/cuda*.list && \
    curl https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-keyring_1.0-1_all.deb \
    -o cuda-keyring_1.0-1_all.deb && \
    dpkg -i cuda-keyring_1.0-1_all.deb

ARG CONFIG
ARG COMMIT=0.13.0
ARG PORT
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG
ENV PORT=$PORT
ENV COMMIT=$COMMIT

COPY ./requirements.txt /src/requirements.txt
RUN pip install --upgrade pip && pip install -r /src/requirements.txt

RUN rm -r /etc/apt/sources.list.d && apt-get update && apt-get install git -y
RUN pip install https://codeload.github.com/deeppavlov/DeepPavlov/tar.gz/${COMMIT}

COPY . /src

WORKDIR /src

RUN python -m deeppavlov install $CONFIG

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn --workers=1 --timeout 500 server:app -b 0.0.0.0:8078