FROM python:3.8.0

WORKDIR /src
RUN mkdir /global_data
COPY ./skills/coronavirus_skill/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./skills/coronavirus_skill/ ./
COPY ./common/ ./common/

CMD gunicorn --workers=1 --bind 0.0.0.0:8061 --timeout=60 server:app
