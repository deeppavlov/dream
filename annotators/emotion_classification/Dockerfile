FROM deeppavlov/base-gpu:0.12.0

WORKDIR /app
COPY . .

RUN python -m deeppavlov install emo_bert.json && \
    python -m deeppavlov download emo_bert.json