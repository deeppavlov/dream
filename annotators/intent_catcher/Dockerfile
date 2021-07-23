FROM tensorflow/tensorflow:1.15.2-gpu-py3

EXPOSE 3007:3007

WORKDIR /

RUN  apt-get update && \
     apt-get install -y wget git && \
     rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install git+git://github.com/deepmipt/DeepPavlov.git@dbcaf73acd8580e2bec337300ab0d29887d78c51

RUN python -c "import tensorflow_hub as hub; hub.Module(\"https://tfhub.dev/google/universal-sentence-encoder/2\")" && \
    wget -O /usr/local/lib/python3.6/dist-packages/deeppavlov/utils/server/server.py \
    https://raw.githubusercontent.com/deepmipt/DeepPavlov/1e707d55ca090782f16f918f15450d1d07d27c85/deeppavlov/utils/server/server.py

COPY ./ /

CMD python -m deeppavlov riseapi intent_catcher -d -p 3007
