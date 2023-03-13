FROM deeppavlov/base-gpu:0.17.5

RUN pip install git+https://github.com/deeppavlov/DeepPavlov.git@1f0bda76c7c3fd6ccd4a1c0c880c0fffb73522d1

WORKDIR /base/DeepPavlov

ARG CONFIG

ARG SERVICE_PORT
ENV CONFIG=$CONFIG
ENV SERVICE_PORT=$SERVICE_PORT

WORKDIR /src
RUN mkdir common

COPY annotators/combined_classification/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY annotators/combined_classification/ ./
COPY common/ common/

CMD gunicorn --workers=1 --bind 0.0.0.0:8087 --timeout=1200 server:app

