FROM python:3.9.16-slim

WORKDIR /src

ARG LANGUAGE=EN
ENV LANGUAGE ${LANGUAGE}

COPY ./skills/meta_script_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt && \
    python -m spacy download en && \
    python -m nltk.downloader vader_lexicon

COPY ./skills/meta_script_skill/ /src/
COPY ./common/ /src/common/

CMD gunicorn --workers=2 server:app
