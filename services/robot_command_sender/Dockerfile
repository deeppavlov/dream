FROM python:3.9

WORKDIR /src

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

COPY services/robot_commander_sender/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY services/robot_commander_sender/. /src/.

CMD uvicorn --workers=1 server:app --host 0.0.0.0 --port ${SERVICE_PORT} --timeout=300
