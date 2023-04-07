FROM deeppavlov/base-gpu:latest

ARG CONFIG
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG

RUN mkdir /src /midas

COPY ./requirements.txt /src/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /src/requirements.txt && \
    python -m spacy download ru_core_news_sm

COPY . /src/

WORKDIR /src

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8011
