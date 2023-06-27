FROM python:3.7.4

WORKDIR /src

RUN rm -r /etc/apt/sources.list.d && \
    apt update && apt install -y libsndfile-dev

COPY ./requirements.txt /src/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /src/requirements.txt && \
    pip install pyopenssl --upgrade && \
    python -m deeppavlov install gobot_md_yaml_minimal && \
    python -m deeppavlov download gobot_md_yaml_minimal

COPY . /src/

CMD gunicorn --workers=1 --bind 0.0.0.0:3002 server:app  --timeout=1000
