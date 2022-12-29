FROM deeppavlov/base-gpu:0.12.0
RUN pip install --upgrade pip && pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.12.0

ARG CONFIG
ARG PORT
ENV CONFIG=$CONFIG
ENV PORT=$PORT

WORKDIR /src
RUN mkdir common

COPY annotators/ConversationEvaluator/requirements.txt .
RUN pip install -r requirements.txt

COPY annotators/ConversationEvaluator/ ./
COPY common/ common/

CMD gunicorn --workers=1 --bind 0.0.0.0:8004 --timeout=1200 server:app
