FROM pytorch/pytorch:1.4-cuda10.1-cudnn7-devel

WORKDIR /app

RUN apt update && apt install -y libsndfile-dev

COPY . .

#TODO: dockefile
# RUN pip install deeppavlov==0.12.1 && \
#     python -m deeppavlov install asr_tts && \
#     python -m deeppavlov download asr.json && \
#     python -m deeppavlov download tts.json

RUN pip install -r requirements.txt