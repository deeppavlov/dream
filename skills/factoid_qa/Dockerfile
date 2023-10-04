FROM python:3.9.16-slim

RUN mkdir /src /src/common

COPY ./skills/factoid_qa/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/factoid_qa/ /src/
COPY ./common/ /src/common/
WORKDIR /src

ENV DP_SKIP_NLTK_DOWNLOAD='True'
CMD gunicorn --workers=2 server:app
