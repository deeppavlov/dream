FROM python:3.7-slim-stretch

ARG PORT
ENV PORT=$PORT

EXPOSE $PORT

COPY common/alexa_kit/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./common/alexa_kit /src
WORKDIR /src

CMD uvicorn server:app \
    --ssl-keyfile private-key.pem \
    --ssl-certfile certificate.pem \
    --host 0.0.0.0 \
    --port $PORT \
    --interface wsgi \
    --log-level info \
    --reload
