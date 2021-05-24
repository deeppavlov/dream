FROM deeppavlov/base-gpu:0.12.1

ARG CONFIG
ARG COMMIT
ARG PORT
ARG SRC_DIR

ARG SED_ARG=" | "

ENV CONFIG=$CONFIG
ENV PORT=$PORT
ENV COMMIT=$COMMIT

COPY ./annotators/kbqa/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN cd DeepPavlov && \
    git config --global user.email "you@example.com" && \
    git config --global user.name "Your Name" && \
    git fetch --all --tags --prune && \
    git checkout $COMMIT && \
    pip install -e .

COPY $SRC_DIR /src

WORKDIR /src

RUN sed -i "s|$SED_ARG|g" "$CONFIG"

RUN python -m deeppavlov install $CONFIG
RUN python -m spacy download en_core_web_sm

CMD gunicorn  --workers=1 --timeout 500 server:app -b 0.0.0.0:8072
