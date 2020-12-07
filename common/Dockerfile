FROM deeppavlov/base-gpu:0.12.1

ARG CONFIG
ARG COMMIT
ARG PORT
ARG SRC_DIR

ENV CONFIG=$CONFIG
ENV PORT=$PORT

RUN pip install sentry-sdk==0.13.0

RUN cd DeepPavlov && \
    git config --global user.email "you@example.com" && \
    git config --global user.name "Your Name" && \
    git fetch --all --tags --prune && \
    git checkout 0.12.1 && \
    git merge 16759efdc5a12583a6c19af7f3de5b7673a7591e -m 'merging metrics' && \
    git merge 9215c4f22a0f49f28826d3b3a048e78bce1629d2 -m 'merging lockfile' && \
    git merge 2562ee8b1b5fa9c724aa0d8054245f4a036bc785 -m 'merging ckbqa_fix' && \
    pip install -e .

COPY $SRC_DIR /src

WORKDIR /src

RUN python -m deeppavlov install $CONFIG

CMD python -m deeppavlov riseapi $CONFIG -p $PORT -d
