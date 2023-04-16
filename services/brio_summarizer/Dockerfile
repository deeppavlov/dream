FROM python:3.7.4

COPY ${WORK_DIR}/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
COPY ${WORK_DIR} /src
WORKDIR /src
