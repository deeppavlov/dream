FROM python:3.7.4

ARG DATA_URL=http://files.deeppavlov.ai/alexaprize_data/elmo2.tar.gz
ARG NER_URL=http://files.deeppavlov.ai/alexaprize_data/ner.tar.xz

WORKDIR /src

RUN curl -L $NER_URL --output /tmp/ner.tar.xz && tar -xf /tmp/ner.tar.xz -C / && rm /tmp/ner.tar.xz

RUN mkdir /elmo2
RUN curl -L $DATA_URL --output /tmp/elmo2.tar.gz && tar -xf /tmp/elmo2.tar.gz -C /elmo2 && rm /tmp/elmo2.tar.gz
RUN mkdir /src/tfhub_cache_dir
ENV TFHUB_CACHE_DIR tfhub_cache_dir

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"

COPY . .

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8000
