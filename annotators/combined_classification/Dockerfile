FROM deeppavlov/base-gpu:0.17.5

RUN pip install git+https://github.com/dimakarp1996/DeepPavlov.git@50f28296a4303211156aee2aa7d1bfb89bfae205

WORKDIR /base/DeepPavlov

ARG CONFIG

ARG PORT
ENV CONFIG=$CONFIG
ENV PORT=$PORT

WORKDIR /src
RUN mkdir common

COPY annotators/combined_classification/ ./
COPY common/ common/

RUN pip install -r requirements.txt
RUN python -m deeppavlov download $CONFIG

CMD gunicorn --workers=1 --bind 0.0.0.0:8087 --timeout=300 server:app
