FROM deeppavlov/base-gpu:0.12.1

ARG CONFIG
ARG COMMIT=0.13.0
ARG PORT
ARG SRC_DIR

ENV CONFIG=$CONFIG
ENV PORT=$PORT

COPY ./annotators/odqa/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN cd DeepPavlov && \
    git config --global user.email "you@example.com" && \
    git config --global user.name "Your Name" && \
    git fetch --all --tags --prune && \
    git checkout $COMMIT && \
    pip install -e .

COPY $SRC_DIR /src

WORKDIR /src

RUN python -m deeppavlov install $CONFIG

CMD ./proxy.sh
