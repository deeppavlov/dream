FROM python:3.8.0

RUN mkdir /src
RUN mkdir /global_data
COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src/
WORKDIR /src

CMD gunicorn --workers=1 --bind 0.0.0.0:8061 --timeout=60 server:app
