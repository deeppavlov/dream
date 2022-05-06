FROM deeppavlov/base-gpu:0.17.2

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

WORKDIR /src

ARG CONFIG_NAME
ENV CONFIG_NAME ${CONFIG_NAME}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}


COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src
WORKDIR /src

RUN python -m deeppavlov install ${CONFIG_NAME}
RUN python -m deeppavlov download ${CONFIG_NAME}
RUN python train_model_if_not_exist.py


CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=300
