FROM tensorflow/tensorflow:1.15.2-gpu-py3

RUN apt-key del 7fa2af80  && \
    rm -f /etc/apt/sources.list.d/cuda*.list && \
    curl https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-keyring_1.0-1_all.deb \
    -o cuda-keyring_1.0-1_all.deb && \
    dpkg -i cuda-keyring_1.0-1_all.deb \

EXPOSE 3007:3007

WORKDIR /

RUN  apt-get update && \
     apt-get install -y wget git && \
     rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install git+git://github.com/deeppavlov/DeepPavlov.git@dbcaf73acd8580e2bec337300ab0d29887d78c51

RUN python -c "import tensorflow_hub as hub; hub.Module(\"https://tfhub.dev/google/universal-sentence-encoder/2\")" && \
    wget -O /usr/local/lib/python3.6/dist-packages/deeppavlov/utils/server/server.py \
    https://raw.githubusercontent.com/deeppavlov/DeepPavlov/1e707d55ca090782f16f918f15450d1d07d27c85/deeppavlov/utils/server/server.py

COPY ./ /

CMD python -m deeppavlov riseapi intent_catcher -d -p 3007
