FROM pytorch/pytorch:1.6.0-cuda10.1-cudnn7-devel

RUN rm -r /etc/apt/sources.list.d && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        locales curl wget && \
    printf '%s\n%s\n' 'en_US.UTF-8 UTF-8' 'ru_RU.UTF-8 UTF-8' >> /etc/locale.gen && \
    locale-gen && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false &&  \
	rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache

ENV LANG='en_US.UTF-8' LANGUAGE='en_US.UTF-8' LC_ALL='en_US.UTF-8'

RUN mkdir /src
RUN mkdir /model_data/
RUN wget http://lnsigo.mipt.ru/export/prochtenie/xlnet_0_gector.tar.gz
RUN tar zxfv xlnet_0_gector.tar.gz -C /model_data/
RUN wget http://lnsigo.mipt.ru/export/prochtenie/roberta_1_gector.tar.gz
RUN tar zxfv roberta_1_gector.tar.gz -C /model_data/
COPY ./requirements.txt /src/requirements.txt
RUN cat /src/requirements.txt | cut -f1 -d"#" | sed '/^\s*$/d' | xargs -n 1 pip install

RUN python -m spacy download en

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

ARG STORE_DATA_ENABLE
ENV STORE_DATA_ENABLE ${STORE_DATA_ENABLE}

COPY . /src/
WORKDIR /src

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

CMD ./server_run.sh