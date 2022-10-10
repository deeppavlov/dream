FROM deeppavlov/base-gpu:1.0.0rc1
RUN pip install --upgrade pip && pip install git+https://github.com/deeppavlov/DeepPavlov.git@1.0.0rc1

ARG CONFIG
ARG PORT
ARG SRC_DIR
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG
ENV PORT=$PORT

COPY ./annotators/NER_deeppavlov/requirements.txt /src/requirements.txt
RUN pip install --upgrade pip && pip install -r /src/requirements.txt

COPY $SRC_DIR /src

WORKDIR /src

RUN python -m deeppavlov download $CONFIG

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:8021
