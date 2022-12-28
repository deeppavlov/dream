FROM pytorch/pytorch:1.4-cuda10.1-cudnn7-devel

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt && \
    rm requirements.txt && \
    git clone https://github.com/CorentinJ/Real-Time-Voice-Cloning.git . && \
    git checkout 8f71d678d2457dffc4d07b52e75be11433313e15 && \
    pip install -r requirements.txt

RUN apt-key del 7fa2af80  && \
    rm -f /etc/apt/sources.list.d/cuda*.list && \
    curl https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-keyring_1.0-1_all.deb \
    -o cuda-keyring_1.0-1_all.deb && \
    dpkg -i cuda-keyring_1.0-1_all.deb

RUN apt update && \
    apt install unzip \
                wget

RUN wget http://files.deeppavlov.ai/deeppavlov_data/nemo/voice_cloning/pretrained.zip && \
    unzip pretrained.zip && \
    rm pretrained.zip

RUN apt install -y libsndfile-dev

RUN wget http://files.deeppavlov.ai/deeppavlov_data/nemo/voice_cloning/gerty_sample.wav

COPY main.py .