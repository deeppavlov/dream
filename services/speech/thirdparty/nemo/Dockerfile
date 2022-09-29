# FROM pytorch/pytorch:1.4-cuda10.1-cudnn7-devel
FROM python:3.8

ENV DEBIAN_FRONTEND noninteractive

# RUN apt-get update -y --fix-missing && \
#     apt-get install -y -q \
#         build-essential \
#         openssl \
#         git \
#         libssl-dev \
#         libffi-dev \
#         cron && \
#     rm -rf /var/lib/apt/lists/*


# RUN apt update && apt install -y libsndfile-dev

# RUN apt-key del 7fa2af80  && \
#     rm -f /etc/apt/sources.list.d/cuda*.list && \
#     curl https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-keyring_1.0-1_all.deb \
#     -o cuda-keyring_1.0-1_all.deb && \
#     dpkg -i cuda-keyring_1.0-1_all.deb

# RUN apt-get -y update

# COPY . .

# RUN pip install deeppavlov==0.12.1 && \
#     python -m deeppavlov install asr_tts && \
#     python -m deeppavlov download asr.json && \
#     python -m deeppavlov download tts.json

COPY . .
RUN pip install -r requirements.txt
RUN pip install uvicorn