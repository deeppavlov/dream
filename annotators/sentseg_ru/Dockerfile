FROM deeppavlov/base-gpu:0.14.1

ARG CONFIG
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG

RUN mkdir /src
RUN mkdir /midas

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src/

WORKDIR /src

RUN python -m deeppavlov install $CONFIG
RUN python -m spacy download ru_core_news_sm

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8011
