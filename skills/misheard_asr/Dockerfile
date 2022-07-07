FROM python:3.8.0

RUN mkdir /src
RUN mkdir /src/common

COPY ./skills/misheard_asr/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/misheard_asr/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=2 server:app
