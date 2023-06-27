FROM python:3.10

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src/

CMD gunicorn --workers=1 --bind 0.0.0.0:3002 server:app
