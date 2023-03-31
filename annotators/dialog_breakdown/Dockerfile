FROM deeppavlov/base-gpu:0.12.0
RUN pip install --upgrade pip && pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.12.0

ARG CONFIG
ARG SERVICE_PORT
ARG SED_ARG=" | "

ENV CONFIG=$CONFIG
ENV SERVICE_PORT=$SERVICE_PORT

WORKDIR /src
RUN mkdir common

COPY annotators/dialog_breakdown/requirements.txt .
RUN pip install -r requirements.txt

COPY annotators/dialog_breakdown/ ./
COPY common/ common/

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

CMD gunicorn --workers=1 --bind 0.0.0.0:8082 --timeout=1200 server:app
