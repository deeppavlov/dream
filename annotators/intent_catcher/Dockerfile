FROM tensorflow/tensorflow:1.15.2-gpu-py3

EXPOSE 3006:3006

WORKDIR /

RUN  apt-get update \
  && apt-get install -y wget \
  && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY ./ /

RUN python -c "import tensorflow_hub as hub; hub.Module(\"https://tfhub.dev/google/universal-sentence-encoder/2\")"

CMD gunicorn --workers=1 --name=catcher --bind 0.0.0.0:3007 --timeout=500 server:app
