FROM python:3.9.16-slim

WORKDIR /src

COPY ./skills/misheard_asr/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/misheard_asr/ /src/
COPY ./common/ /src/common/

CMD gunicorn --workers=2 server:app
