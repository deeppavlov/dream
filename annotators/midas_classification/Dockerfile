FROM deeppavlov/base-gpu:0.14.1

ARG CONFIG
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG

RUN mkdir /src /midas

COPY ./requirements.txt /src/requirements.txt

RUN pip install --upgrade pip && \
    pip install -r /src/requirements.txt && \
    python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet')" && \
    python -m spacy download en_core_web_sm
COPY . /src/

WORKDIR /src


RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8090