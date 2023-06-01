FROM python:3.9.16-slim

WORKDIR /src

COPY ./annotators/fact_random/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./annotators/fact_random/ .
COPY ./common/ ./common/

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:8119
