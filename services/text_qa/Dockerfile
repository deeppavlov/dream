FROM tensorflow/tensorflow:1.15.2-gpu

ARG CONFIG
ARG COMMIT=0.13.0
ARG PORT
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG
ENV PORT=$PORT
ENV COMMIT=$COMMIT

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN rm -r /etc/apt/sources.list.d && apt-get update && apt-get install git -y
RUN pip install git+https://github.com/deepmipt/DeepPavlov.git@${COMMIT}

COPY . /src

WORKDIR /src

RUN python -m deeppavlov install $CONFIG
RUN python -m spacy download en_core_web_sm

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn --workers=1 --timeout 500 server:app -b 0.0.0.0:8078