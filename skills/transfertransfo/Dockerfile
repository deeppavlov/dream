FROM pytorch/pytorch:1.2-cuda10.0-cudnn7-runtime

LABEL maintainer="Kuznetsov Denis <kuznetsov.den.p@gmail.com>"

########### UVICORN ###########

RUN pip install uvicorn gunicorn

COPY ./uvicorn/start.sh /start.sh
RUN chmod +x /start.sh

COPY ./uvicorn/gunicorn_conf.py /gunicorn_conf.py

COPY ./uvicorn/start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh

EXPOSE 80

########### MODEL ###########

RUN mkdir -p /root/models && \
    curl https://s3.amazonaws.com/models.huggingface.co/transfer-learning-chatbot/finetuned_chatbot_gpt.tar.gz > /root/models/finetuned_chatbot_gpt.tar.gz && \
    cd /root/models/ && \
    tar -xvzf finetuned_chatbot_gpt.tar.gz


COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV PYTHONPATH /opt/conda/lib/python3.6
ENV MODEL_PATH /root/models
ENV DEVICE cpu

WORKDIR /app

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]