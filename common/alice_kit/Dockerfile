FROM python:3.7-slim-stretch

ARG PORT
ENV PORT=$PORT

EXPOSE $PORT

COPY common/alice_kit/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./common/alice_kit /src
WORKDIR /src

CMD uvicorn server:app \
    --ssl-keyfile private-key.pem \
    --ssl-certfile certificate.pem \
    --host 0.0.0.0 \
    --port $PORT \
    --log-level info \
    --reload
