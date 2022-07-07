FROM python:3.8.0

WORKDIR /src

ARG LANGUAGE=EN
ENV LANGUAGE ${LANGUAGE}

COPY ./skills/emotion_skill/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./skills/emotion_skill/ ./
COPY ./common/ ./common/

CMD gunicorn --workers=1 --bind 0.0.0.0:8049 --timeout=60 server:app
