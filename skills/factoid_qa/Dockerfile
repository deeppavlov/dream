FROM python:3.7.4

RUN mkdir /src
RUN mkdir /src/common

COPY ./skills/factoid_qa/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/factoid_qa/ /src/
COPY ./common/ /src/common/
WORKDIR /src

RUN python -m deeppavlov download yahoo_convers_vs_info_light.json

CMD gunicorn --workers=2 server:app
