FROM python:3.7.4

RUN mkdir /src

COPY annotators/bot_emotion_classifier/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY annotators/bot_emotion_classifier /src/
WORKDIR /src

CMD gunicorn --workers=2 server:app