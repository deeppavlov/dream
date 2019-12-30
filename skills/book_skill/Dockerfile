FROM python:3.8.0

RUN mkdir /src
RUN mkdir /global_data
RUN wget http://lnsigo.mipt.ru/export/datasets/author_namesbooks.zip -O /global_data/author_namesbooks.zip
COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src/
WORKDIR /src

CMD gunicorn --workers=1 --bind 0.0.0.0:8023 --timeout=60 server:app
