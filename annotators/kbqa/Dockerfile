FROM nvidia/cuda:10.0-devel-ubuntu16.04

EXPOSE 5000

WORKDIR /base

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        dpkg-dev \
        gcc \
        git	\
        libbz2-dev \
        libc6-dev \
        libcudnn7=7.6.2.24-1+cuda${CUDA_VERSION%.*} \
        libcudnn7-dev=7.6.2.24-1+cuda${CUDA_VERSION%.*} \
        libexpat1-dev \
        libffi-dev \
        libgdbm-dev \
        liblzma-dev \
        libncursesw5-dev \
        libreadline-dev \
        libsndfile-dev \
        libsqlite3-dev \
        libssl-dev \
        locales \
        make \
        tk-dev \
        wget \
        xz-utils \
        zlib1g-dev && \
    locale-gen en_US.UTF-8 && \
    locale-gen ru_RU.UTF-8 && \
    wget --no-check-certificate -O python.tar.xz https://www.python.org/ftp/python/3.7.4/Python-3.7.4.tar.xz && \
    mkdir -p /usr/src/python && \
	tar -xC /usr/src/python --strip-components=1 -f python.tar.xz && \
    rm python.tar.xz && \
    cd /usr/src/python && \
	./configure && \
	make -j "$(nproc)" altinstall && \
	ln -s /usr/local/bin/python3.7 /usr/local/bin/python && \
    ln -s /usr/local/bin/pip3.7 /usr/local/bin/pip && \
    pip install virtualenv==16.7.5 && \
    virtualenv /base/venv && \
	mkdir -p /venv/dp_internal_token_dir && \
    cd /base && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
	rm -rf /usr/src/python \
	    /var/lib/apt/lists/*

ENV PATH=/base/venv/bin:$PATH
ENV LANG='en_US.UTF-8' LANGUAGE='en_US.UTF-8' LC_ALL='en_US.UTF-8'

RUN git clone https://github.com/deepmipt/DeepPavlov.git && \
    cd DeepPavlov && \
    git checkout ckbqa_fix && \
    python setup.py develop && \
    python -c 'import deeppavlov.models' && \
    pip install -r deeppavlov/requirements/tf-gpu.txt && \
    rm -rf /root/.cache

ENV DP_SKIP_NLTK_DOWNLOAD='True'

ARG skillconfig
ARG skillport
ARG skill_endpoint
ARG skillhost
ARG skilldir
ARG SED_ARG=" | "
ARG skip_download=''

ENV CONFIG=$skillconfig
ENV PORT=$skillport
ENV HOST=$skillhost
ENV ENDPOINT=$skill_endpoint
ENV TFHUB_CACHE_DIR=/tmp/tfhub
ENV DIR=$skilldir

VOLUME /tmp/tfhub

RUN mkdir dp-agent
WORKDIR /dp-agent
ENV PYTHONPATH "${PYTONPATH}:/dp-agent"

RUN mkdir -p /dp-agent/$DIR
COPY $DIR /dp-agent/$DIR
RUN [ -z "$skip_download" ] && python -m deeppavlov download $CONFIG || echo 'skipping file download'
RUN python -m deeppavlov install $CONFIG

COPY dp/ /dp-agent/dp
RUN python /dp-agent/dp/dp_server_config.py

RUN pip install sentry-sdk==0.13.0 # TODO: Move it to separate requirements
RUN pip install -r /base/DeepPavlov/deeppavlov/requirements/spelling.txt
CMD [ -z "$DOWNLOAD_AT_START" ] && python -m deeppavlov riseapi $CONFIG -p $PORT || python -m deeppavlov riseapi $CONFIG -p $PORT -d
