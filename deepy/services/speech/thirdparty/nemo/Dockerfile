FROM pytorch/pytorch:1.9.0-cuda10.2-cudnn7-runtime

WORKDIR /app

RUN apt update && \
    apt install -y wget \
                   git \
                   gnupg \
                   software-properties-common && \
    wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - && \
    apt-add-repository "deb http://apt.llvm.org/bionic/ llvm-toolchain-bionic-11 main" && \
    apt update && \
    apt install -y libsndfile-dev \
                   llvm-11-dev

COPY requirements.txt requirements.txt

RUN LLVM_CONFIG=/usr/bin/llvm-config-11 pip install -r requirements.txt && \
    python -c 'import nemo.collections.asr as nemo_asr; quartznet = nemo_asr.models.EncDecCTCModel.from_pretrained(model_name="QuartzNet15x5Base-En")'

COPY main.py main.py