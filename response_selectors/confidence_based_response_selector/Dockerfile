FROM python:3.9.16-slim

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

ARG LANGUAGE=EN
ENV LANGUAGE ${LANGUAGE}
ARG FILTER_BADLISTED_WORDS
ENV FILTER_BADLISTED_WORDS ${FILTER_BADLISTED_WORDS}

COPY . /src/

CMD gunicorn --workers=1 --bind 0.0.0.0:3003 server:app
