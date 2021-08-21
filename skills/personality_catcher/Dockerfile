# FROM ubuntu:18.04
FROM tiangolo/uvicorn-gunicorn:python3.7

LABEL maintainer="Kuznetsov Denis <kuznetsov.den.p@gmail.com>"

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]