FROM python:3.8.0

RUN mkdir /src
RUN mkdir /global_data
RUN mkdir /src/common

RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/author_namesbooks.zip -O /global_data/author_namesbooks.zip

COPY ./skills/book_skill/requirements.txt /src/requirements.txt

RUN pip install -r /src/requirements.txt

COPY ./skills/book_skill/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=1 --bind 0.0.0.0:8023 --timeout=60 server:app
