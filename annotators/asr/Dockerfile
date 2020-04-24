FROM python:3.8.0

RUN mkdir /src
RUN mkdir /src/common

COPY ./annotators/asr/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./annotators/asr/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=2 server:app
