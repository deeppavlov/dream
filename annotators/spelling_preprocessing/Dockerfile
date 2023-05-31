FROM python:3.9.1

RUN mkdir /src
COPY . /src/
WORKDIR /src

RUN apt update

RUN apt install python3.9
RUN apt install python-is-python3
RUN apt install python3-pip

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

CMD gunicorn --workers=2 server:app
