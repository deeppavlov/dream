FROM nikolaik/python-nodejs:latest

ARG PORT
ENV PORT=$PORT

EXPOSE $PORT

COPY common/minecraft/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./common/minecraft /src
WORKDIR /src

CMD python bot.py
#CMD uvicorn server:app \
#    --ssl-keyfile private-key.pem \
#    --ssl-certfile certificate.pem \
#    --host 0.0.0.0 \
#    --port $PORT \
#    --interface wsgi \
#    --log-level info \
#    --reload
