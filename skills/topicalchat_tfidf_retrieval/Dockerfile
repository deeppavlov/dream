FROM python:3.7.4

RUN mkdir /src
COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

ARG MODELS_URL
ENV MODELS_URL ${MODELS_URL:-http://lnsigo.mipt.ru/export/models/new_vectorizer_2.zip}

RUN mkdir /global_data
WORKDIR /global_data

RUN wget ${MODELS_URL} -O ./new_vectorizer_2.zip

ARG TOPICAL_DATA_URL
ENV TOPICAL_DATA_URL ${TOPICAL_DATA_URL:-http://lnsigo.mipt.ru/export/alexaprize_data/topicalchat_tfidf_retrieval/topicalchat_music_data.tar.gz}

RUN wget ${TOPICAL_DATA_URL} -O ./topical_data.tar.gz && \
    tar zxfv ./topical_data.tar.gz && \
    rm -f ./topical_data.tar.gz

ARG TOPIC_NAME
ENV TOPIC_NAME ${TOPIC_NAME}

ARG CONFIDENCE_THRESHOLD
ENV CONFIDENCE_THRESHOLD ${CONFIDENCE_THRESHOLD}

ARG TEST_MODE
ENV TEST_MODE ${TEST_MODE}

COPY . /src/
WORKDIR /src

CMD gunicorn --workers=2 server:app
