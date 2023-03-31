FROM deeppavlov/base-gpu:0.17.2
RUN pip install --upgrade pip && pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.17.2

COPY $SRC_DIR /src
WORKDIR /src

ARG CONFIG
ARG SRC_DIR
ARG SERVICE_PORT

ENV CONFIG=$CONFIG
ENV SERVICE_PORT=$SERVICE_PORT

ARG SED_ARG=" | "
ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

COPY services/${SERVICE_NAME}/requirements.txt .
RUN pip install -r requirements.txt

COPY services/${SERVICE_NAME}/ ./
COPY ./common/ ./common/

RUN python -m deeppavlov install $CONFIG

RUN python -m spacy download en_core_web_sm

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn --workers=1 --timeout 300 server:app -b 0.0.0.0:${SERVICE_PORT}
