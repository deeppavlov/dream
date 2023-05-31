FROM python:3.9.16-slim

WORKDIR /src
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# ARG TEST_MODE
# ENV TEST_MODE ${TEST_MODE}

COPY . .

CMD gunicorn --workers=2 server:app
