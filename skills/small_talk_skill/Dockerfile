FROM python:3.9.16-slim

WORKDIR /src

COPY ./skills/small_talk_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/small_talk_skill/ /src/
COPY ./common/ /src/common/

CMD gunicorn --workers=2 server:app
