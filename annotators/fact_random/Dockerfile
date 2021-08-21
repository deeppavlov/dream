FROM python:3.7.4

RUN mkdir /src
RUN mkdir /src/common

COPY ./annotators/fact_random/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./annotators/fact_random/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:8119
