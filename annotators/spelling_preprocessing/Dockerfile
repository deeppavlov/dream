FROM python:3.9.1

RUN mkdir /src
COPY . /src/
WORKDIR /src

RUN apt update

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

CMD gunicorn --workers=2 server:app --timeout 1200
