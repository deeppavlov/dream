FROM python:3.7.4

RUN mkdir /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -m deeppavlov install gobot_md_yaml_minimal && \
    python -m deeppavlov download gobot_md_yaml_minimal

COPY . /src/
WORKDIR /src

CMD gunicorn --workers=1 --bind 0.0.0.0:3002 server:app  --timeout=1000
