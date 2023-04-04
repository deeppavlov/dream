FROM python:3.8.0

WORKDIR /src

COPY ./skills/misheard_asr/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/misheard_asr/ /src/
COPY ./common/ /src/common/

CMD gunicorn --workers=2 server:app
