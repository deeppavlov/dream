FROM python:3.7.4

ARG DATA_URL=files.deeppavlov.ai/alexaprize_data/sentseg/elmo2.tar.gz
ARG MODEL_META_URL=files.deeppavlov.ai/alexaprize_data/sentseg/model.meta
ARG MODEL_DATA_URL=files.deeppavlov.ai/alexaprize_data/sentseg/model.data-00000-of-00001

WORKDIR /src
RUN mkdir /data
RUN mkdir /elmo2

RUN curl -L $DATA_URL --output /tmp/elmo2.tar.gz && tar -xf /tmp/elmo2.tar.gz -C /elmo2 && rm /tmp/elmo2.tar.gz
RUN curl -L $MODEL_META_URL --output /data/model.meta
RUN curl -L $MODEL_DATA_URL --output /data/model.data-00000-of-00001

RUN mkdir tfhub_cache_dir
ENV TFHUB_CACHE_DIR tfhub_cache_dir

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"

COPY . .
COPY model.index /data/

CMD gunicorn --workers=1 server:app
