FROM python:3.9.16-slim

WORKDIR /src

COPY ./requirements.txt .
RUN pip install -r /src/requirements.txt

COPY . .

CMD gunicorn --workers=2 server:app
