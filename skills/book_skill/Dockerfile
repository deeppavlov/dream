FROM python:3.8.0

RUN mkdir /src
RUN mkdir /src/common
RUN mkdir /global_data
ARG QUERY_DICT

COPY ./skills/book_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/book_skill/ /src/
COPY ./common/ /src/common/
RUN curl $QUERY_DICT --output /global_data/book_query_dict.pkl
WORKDIR /src

CMD gunicorn --workers=1 --bind 0.0.0.0:8032 --timeout=300 server:app
