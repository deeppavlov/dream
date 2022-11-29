FROM deeppavlov/base-gpu:0.14.1
RUN pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.14.1

ARG CONFIG
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG

RUN mkdir /src
RUN mkdir /midas

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet')"
COPY . /src/

WORKDIR /src

RUN python -m spacy download en_core_web_sm

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8090
