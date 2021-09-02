FROM python:3.7.4

RUN mkdir /src

COPY ./GoEmotions/requirements.txt /src/GoEmotions/requirements.txt
RUN pip install -r /src/GoEmotions/requirements.txt

COPY . /src/
WORKDIR /src

CMD gunicorn --workers=2 server:app