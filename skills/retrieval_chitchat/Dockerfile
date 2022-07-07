# FROM ubuntu:18.04
FROM tiangolo/uvicorn-gunicorn:python3.7

ENV PYTHONPATH /usr/local/lib/python3.7

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /root/models && \
    curl http://files.deeppavlov.ai/deeppavlov_data/retrieval_chitchat_personachat_v1.tar.gz > /root/models/retrieval_chitchat_personachat_v1.tar.gz && \
    curl http://files.deeppavlov.ai/deeppavlov_data/personachat_embeddings.tar.gz > /root/models/personachat_embeddings.tar.gz && \
    curl http://files.deeppavlov.ai/deeppavlov_data/confidence.tar.gz > /root/models/confidence.tar.gz && \
    cd /root/models/ && \
    tar -xvzf retrieval_chitchat_personachat_v1.tar.gz && \
    tar -xvzf personachat_embeddings.tar.gz && \
    tar -xvzf confidence.tar.gz

COPY . /app

ENV MODEL_PATH /root/models/personachat_v1
ENV DATABASE_PATH /root/models/personachat_embeddings.pickle
ENV CONFIDENCE_PATH /root/models/confidence.npy

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]