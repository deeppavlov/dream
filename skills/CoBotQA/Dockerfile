FROM python:3.7.4

WORKDIR /src
COPY requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt

CMD gunicorn --workers=2 server:app
