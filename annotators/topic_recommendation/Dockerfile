FROM python:3.7.4

RUN mkdir /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src/
WORKDIR /src

ARG DATA_URL=files.deeppavlov.ai/alexaprize_data/logreg_recommendation_model.pkl

RUN mkdir /data
RUN curl -L $DATA_URL --output /data/logreg_recommendation_model.pkl

ENV MODEL_PATH /data/logreg_recommendation_model.pkl

CMD gunicorn --workers=2 server:app
