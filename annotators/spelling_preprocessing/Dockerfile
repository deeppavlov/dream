FROM python:3.9.16

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt
RUN apt install -y curl && pip install -r /src/requirements.txt

COPY . /src/

CMD gunicorn --workers=2 server:app