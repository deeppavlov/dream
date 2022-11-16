FROM deeppavlov/base-gpu:0.17.5

RUN pip install git+https://github.com/dimakarp1996/DeepPavlov.git@bb12c9845487d952c53a46917fb04d0ff1cca192

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
