FROM python:3.7.4

ARG SUMMARIZATION_REQUEST_TIMEOUT
ENV SUMMARIZATION_REQUEST_TIMEOUT ${SUMMARIZATION_REQUEST_TIMEOUT}

COPY ${WORK_DIR}/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
COPY ${WORK_DIR} /src
WORKDIR /src
