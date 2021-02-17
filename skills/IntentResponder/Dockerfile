FROM python:3.6

WORKDIR /src

COPY skills/IntentResponder/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./skills/IntentResponder/ .
COPY common common

COPY ./common/ common/

EXPOSE 8012:8012

CMD gunicorn --workers=1 --name=responder --bind 0.0.0.0:8012 --timeout=500 server:app
