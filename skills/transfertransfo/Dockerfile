FROM pytorch/pytorch:1.2-cuda10.0-cudnn7-runtime

########### DOWNLOADING MODELS ###########

ARG MODE
ENV MODE ${MODE:-staging}

RUN mkdir -p /root/models && \
    [ $MODE = dev ] && \
    MODEL_URL=http://files.deeppavlov.ai/alexaprize_data/finetuned_chatbot_gpt.tar.gz || \
    MODEL_URL=https://s3.amazonaws.com/models.huggingface.co/transfer-learning-chatbot/finetuned_chatbot_gpt.tar.gz && \
    curl $MODEL_URL > /root/models/finetuned_chatbot_gpt.tar.gz && \
    cd /root/models/ && \
    tar -xvzf finetuned_chatbot_gpt.tar.gz

########### MODELS ###########

RUN mkdir /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

RUN python -m nltk.downloader all

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV MODEL_PATH /root/models
ENV PYTHONPATH /opt/conda/lib/python3.6
ENV DEVICE cpu

COPY . /app/
WORKDIR /app

CMD gunicorn --workers=2 server:app --timeout 120
