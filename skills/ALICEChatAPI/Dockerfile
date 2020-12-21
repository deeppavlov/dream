FROM python:3.7.4

WORKDIR /src

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD gunicorn --workers=2 server:app
