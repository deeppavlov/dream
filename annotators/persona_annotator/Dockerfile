FROM deeppavlov/base-gpu:0.12.0

WORKDIR /app
COPY . .

RUN python -m deeppavlov install persona_annotator.json && \
    python -m deeppavlov download persona_annotator.json