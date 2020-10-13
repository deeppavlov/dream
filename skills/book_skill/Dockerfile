FROM python:3.8.0

WORKDIR /src
RUN mkdir /global_data && \
    mkdir /src/common

RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/author_namesbooks.zip -O /global_data/author_namesbooks.zip

COPY ./skills/book_skill/requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY ./skills/book_skill/ ./
COPY ./common/ ./common/

CMD gunicorn --workers=1 --bind 0.0.0.0:8023 --timeout=60 server:app
