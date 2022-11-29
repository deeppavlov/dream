FROM deeppavlov/base-gpu:0.12.0
RUN pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.12.0

ARG CONFIG
ARG DATA_URL=http://files.deeppavlov.ai/alexaprize_data/cobot_conveval2.tar.gz
ARG PORT
ENV CONFIG=$CONFIG
ENV PORT=$PORT

ADD $DATA_URL /tmp

RUN tar -xvzf /tmp/*.tar.gz -C /tmp/

WORKDIR /src
RUN mkdir common

COPY annotators/ConversationEvaluator/requirements.txt .
RUN pip install -r requirements.txt

COPY annotators/ConversationEvaluator/ ./
COPY common/ common/

CMD gunicorn --workers=1 --bind 0.0.0.0:8004 --timeout=300 server:app
