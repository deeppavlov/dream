FROM python:3.7.4

RUN mkdir /src
RUN mkdir /src/common

COPY ./annotators/user_persona_extractor/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./annotators/user_persona_extractor/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=2 server:app
