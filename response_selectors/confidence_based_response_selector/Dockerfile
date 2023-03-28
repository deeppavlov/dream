FROM python:3.7.4

RUN mkdir /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

ARG LANGUAGE=EN
ENV LANGUAGE ${LANGUAGE}
ARG BADLIST_URL
ENV BADLIST_URL ${BADLIST_URL}

COPY . /src/
WORKDIR /src

CMD gunicorn --workers=1 --bind 0.0.0.0:3003 server:app
