FROM tensorflow/tensorflow:1.15.2-gpu

RUN apt-key del 7fa2af80  && \
    rm -f /etc/apt/sources.list.d/cuda*.list && \
    curl https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-keyring_1.0-1_all.deb \
    -o cuda-keyring_1.0-1_all.deb && \
    dpkg -i cuda-keyring_1.0-1_all.deb

RUN apt-get update && apt-get install git -y

ARG CONFIG
ARG CONFIG_WIKI
ARG CONFIG_WHOW
ARG COMMIT=0.13.0
ARG PORT
ARG SRC_DIR
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG
ENV CONFIG_WIKI=$CONFIG_WIKI
ENV CONFIG_WHOW=$CONFIG_WHOW
ENV PORT=$PORT

COPY ./annotators/fact_retrieval/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN pip install git+https://github.com/deeppavlov/DeepPavlov.git@${COMMIT}

COPY $SRC_DIR /src

WORKDIR /src
COPY ./common/ ./common/

RUN sed -i "s|$SED_ARG|g" "$CONFIG"
RUN sed -i "s|$SED_ARG|g" "$CONFIG_WIKI"
RUN sed -i "s|$SED_ARG|g" "$CONFIG_WHOW"

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:8100
