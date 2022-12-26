FROM deeppavlov/base-gpu:0.17.5

RUN pip install git+https://github.com/deeppavlov/DeepPavlov.git@f4dc1a81a006384b4bae7d7e2f49de70e194aeb3

WORKDIR /base/DeepPavlov

ARG CONFIG

ARG PORT
ENV CONFIG=$CONFIG
ENV PORT=$PORT

WORKDIR /src
RUN mkdir common

COPY annotators/combined_classification/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY annotators/combined_classification/ ./
COPY common/ common/

CMD gunicorn --workers=1 --bind 0.0.0.0:8087 --timeout=1200 server:app

