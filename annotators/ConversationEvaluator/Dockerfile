FROM deeppavlov/base-gpu:0.17.2

ARG CONFIG
ARG SERVICE_PORT
ENV CONFIG=$CONFIG
ENV SERVICE_PORT=$SERVICE_PORT

WORKDIR /src

COPY annotators/ConversationEvaluator/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY annotators/ConversationEvaluator/ ./
COPY common/ ./common

CMD gunicorn --workers=1 --bind 0.0.0.0:8004 --timeout=1200 server:app
