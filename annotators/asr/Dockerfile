FROM python:3.8.0

WORKDIR /src

COPY ./annotators/asr/requirements.txt .
RUN pip install -r requirements.txt

COPY ./annotators/asr ./
COPY ./common ./common

CMD gunicorn --workers=2 server:app
