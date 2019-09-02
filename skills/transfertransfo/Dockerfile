# FROM ubuntu:18.04
FROM tiangolo/uvicorn-gunicorn:python3.7

LABEL maintainer="Kuznetsov Denis <kuznetsov.den.p@gmail.com>"

########################################  BASE SYSTEM
# set noninteractive installation
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y apt-utils
RUN apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    tzdata \
    curl

# set local timezone
RUN ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata

# transfer-learning-conv-ai
ENV PYTHONPATH /usr/local/lib/python3.7

RUN mkdir -p /root/models && \
    curl https://s3.amazonaws.com/models.huggingface.co/transfer-learning-chatbot/finetuned_chatbot_gpt.tar.gz > /root/models/finetuned_chatbot_gpt.tar.gz && \
    cd /root/models/ && \
    tar -xvzf finetuned_chatbot_gpt.tar.gz


COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY . /app
    
ENV MODEL_PATH /root/models
EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]