FROM python:3.9.16
WORKDIR /src

COPY annotators/fact_checking/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt 

ARG GENERATIVE_SERVICE_URL
ENV GENERATIVE_SERVICE_URL ${GENERATIVE_SERVICE_URL}
ARG GENERATIVE_TIMEOUT
ENV GENERATIVE_TIMEOUT ${GENERATIVE_TIMEOUT}
ARG GENERATIVE_SERVICE_CONFIG
ENV GENERATIVE_SERVICE_CONFIG ${GENERATIVE_SERVICE_CONFIG}

COPY annotators/fact_checking /src
COPY common /src/common

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8182 --timeout=1200
