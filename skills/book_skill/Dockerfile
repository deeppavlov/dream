FROM python:3.8.0

RUN mkdir /src
RUN mkdir /global_data
RUN mkdir /src/common
ARG AUTHOR_NAMES
ARG QUERY_DICT

COPY ./skills/book_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/book_skill/ /src/
COPY ./common/ /src/common/
COPY ./skills/CoBotQA/ ./src/CoBotQA/
RUN wget -q $AUTHOR_NAMES -O /global_data/book_author_names.txt
RUN wget -q $QUERY_DICT -O /global_data/book_query_dict.pkl
WORKDIR /src

CMD gunicorn --workers=1 --bind 0.0.0.0:8032 --timeout=300 server:app
