FROM python:3.6

RUN mkdir /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src/
WORKDIR /src

COPY ./common/ common/

EXPOSE 8012:8012

CMD gunicorn --workers=1 --name=responder --bind 0.0.0.0:8012 --timeout=500 server:app
