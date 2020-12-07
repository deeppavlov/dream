FROM python:3.7.4

ARG DATA_URL=files.deeppavlov.ai/deeppavlov_data/sentseg/elmo2.tar.gz
ARG MODEL_META_URL=files.deeppavlov.ai/deeppavlov_data/sentseg/model.meta
ARG MODEL_DATA_URL=files.deeppavlov.ai/deeppavlov_data/sentseg/model.data-00000-of-00001

RUN mkdir /src

RUN mkdir /elmo2
RUN curl $DATA_URL > /elmo2/elmo2.tar.gz
RUN curl $MODEL_META_URL > /src/model.meta
RUN curl $MODEL_DATA_URL > /src/model.data-00000-of-00001

RUN tar -xvzf /elmo2/elmo2.tar.gz -C /elmo2
RUN rm /elmo2/elmo2.tar.gz

RUN mkdir /src/tfhub_cache_dir
ENV TFHUB_CACHE_DIR tfhub_cache_dir

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"

COPY . /src/
WORKDIR /src

CMD gunicorn --workers=1 server:app
