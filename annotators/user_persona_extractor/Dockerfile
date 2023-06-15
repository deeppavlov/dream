FROM python:3.9.16-slim

WORKDIR /src

COPY ./annotators/user_persona_extractor/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./annotators/user_persona_extractor/ /src/
COPY ./common/ /src/common/

CMD gunicorn --workers=2 server:app
