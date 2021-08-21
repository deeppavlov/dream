FROM python:3.8.2

RUN mkdir /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src/
WORKDIR /src

CMD gunicorn --workers=2 server:app
