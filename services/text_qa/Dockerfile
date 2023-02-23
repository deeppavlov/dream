FROM deeppavlov/base-gpu:0.17.6

RUN apt-get update && apt-get install git -y

ARG CONFIG
ARG PORT
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG
ENV PORT=$PORT

RUN pip freeze | grep deeppavlov

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src

WORKDIR /src

RUN python -m deeppavlov install $CONFIG
RUN python -m spacy download en_core_web_sm

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn --workers=1 --timeout 500 server:app -b 0.0.0.0:8078
