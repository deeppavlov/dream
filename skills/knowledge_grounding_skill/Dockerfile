FROM python:3.9.16-slim

WORKDIR /src

COPY ./skills/knowledge_grounding_skill/requirements.txt .
RUN pip install -r requirements.txt && \
    python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"

COPY ./skills/knowledge_grounding_skill ./
COPY ./common/ common/

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8085
