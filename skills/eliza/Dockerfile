FROM python:3.7.4

WORKDIR /src
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# ARG TEST_MODE
# ENV TEST_MODE ${TEST_MODE}

COPY . .

CMD gunicorn --workers=2 server:app
