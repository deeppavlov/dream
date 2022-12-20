FROM deeppavlov/base-gpu:0.17.5

RUN pip install git+https://github.com/deeppavlov/DeepPavlov.git@a53c42062e4bccf6ec63021ec6bd7b9fbe23f091

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

RUN pip install -r requirements.txt

CMD gunicorn --workers=1 --bind 0.0.0.0:8087 --timeout=1200 server:app

