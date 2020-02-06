FROM python:3.7.4

RUN mkdir /src
COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

# ARG TEST_MODE
# ENV TEST_MODE ${TEST_MODE}

COPY . /src/
WORKDIR /src



CMD gunicorn --workers=2 server:app
