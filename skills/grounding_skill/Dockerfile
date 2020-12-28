FROM python:3.8.0

RUN mkdir /src
RUN mkdir /src/common
RUN mkdir /global_data
COPY ./skills/grounding_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/grounding_skill/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=1 --bind 0.0.0.0:8080 --timeout=60 server:app
