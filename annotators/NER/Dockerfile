FROM python:3.9.16-slim

ARG DATA_URL=http://files.deeppavlov.ai/alexaprize_data/elmo2.tar.gz
ARG NER_URL=http://files.deeppavlov.ai/alexaprize_data/ner.tar.xz

WORKDIR /src

RUN mkdir /elmo2 /src/tfhub_cache_dir
RUN curl -L $NER_URL --output /tmp/ner.tar.xz && \
    tar -xf /tmp/ner.tar.xz -C / && \ rm /tmp/ner.tar.xz \
    curl -L $DATA_URL --output /tmp/elmo2.tar.gz && \
    tar -xf /tmp/elmo2.tar.gz -C /elmo2 && \
    rm /tmp/elmo2.tar.gz \

ENV TFHUB_CACHE_DIR tfhub_cache_dir

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "import nltk; nltk.download('punkt')"

COPY . .

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8000
