FROM deeppavlov/base-gpu:latest

ARG CONFIG
ARG SERVICE_PORT
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG
ENV SERVICE_PORT=$SERVICE_PORT

WORKDIR /src

COPY annotators/dialog_breakdown/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY annotators/dialog_breakdown/ ./
COPY common/ ./common

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn --workers=1 --bind 0.0.0.0:8082 --timeout=1200 server:app
