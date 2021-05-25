FROM tensorflow/tensorflow:1.15.2-gpu

RUN apt-get -y update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:openjdk-r/ppa && \
    apt-get -y update && \
    apt install -y openjdk-11-jdk && \
    apt-get update && apt-get install git -y
    
RUN export JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64/bin/"

ARG CONFIG
ARG COMMIT=0.13.0
ARG PORT
ARG SRC_DIR
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG
ENV PORT=$PORT

COPY ./annotators/fact_retrieval/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN pip install git+https://github.com/deepmipt/DeepPavlov.git@${COMMIT}

COPY $SRC_DIR /src

WORKDIR /src
COPY ./common/ ./common/
RUN pip install pyserini==0.10.1.0
RUN pip uninstall -y tensorflow
RUN pip uninstall -y tensorflow-gpu
RUN pip install tensorflow==1.15.2
RUN pip install tensorflow-gpu==1.15.2
RUN python -m deeppavlov install $CONFIG

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:8100
