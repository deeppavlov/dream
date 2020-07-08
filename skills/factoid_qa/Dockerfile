FROM python:3.7.4

RUN mkdir /src
RUN mkdir /src/common

COPY ./skills/factoid_qa/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/factoid_qa/ /src/
COPY ./common/ /src/common/
WORKDIR /src

RUN wget http://files.deeppavlov.ai/deeppavlov_data/classifiers/yahoo_convers_vs_info_light_v0.tar.gz -q
RUN tar -xvzf yahoo_convers_vs_info_light_v0.tar.gz
RUN rm yahoo_convers_vs_info_light_v0.tar.gz

CMD gunicorn --workers=2 server:app
