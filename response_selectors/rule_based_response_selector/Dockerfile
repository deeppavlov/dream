FROM python:3.7.4

RUN mkdir /src

COPY response_selectors/rule_based_response_selector/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /src/
WORKDIR /src

CMD gunicorn --workers=1 --bind 0.0.0.0:3003 server:app
