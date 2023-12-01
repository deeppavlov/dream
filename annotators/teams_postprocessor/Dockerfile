FROM python:3.9.16-slim

WORKDIR /src

COPY ./annotators/teams_postprocessor/requirements.txt requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./annotators/teams_postprocessor/ /src/
COPY ./common/ /src/common/

CMD gunicorn --workers=1 server:app --bind 0.0.0.0:8000
