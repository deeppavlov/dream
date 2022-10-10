FROM deeppavlov/base-gpu:0.17.2
RUN pip install --upgrade pip && pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.17.2

ARG CONFIG
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG

RUN mkdir /src
RUN mkdir /midas
RUN pip install pip==21.3.1 
COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src/

WORKDIR /src
RUN pip install pymorphy2==0.9.1
RUN python -m spacy download ru_core_news_sm

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8011
