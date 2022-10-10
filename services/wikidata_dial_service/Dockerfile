FROM deeppavlov/base-gpu:0.12.1
RUN pip install --upgrade pip && pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.12.1

ARG CONFIG
ARG COMMIT=0.13.0
ARG PORT

ARG SED_ARG=" | "


ENV CONFIG=$CONFIG
ENV PORT=$PORT

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN cd DeepPavlov && \
    git config --global user.email "you@example.com" && \
    git config --global user.name "Your Name" && \
    git fetch --all --tags --prune && \
    git checkout $COMMIT && \
    pip install -e .

COPY . /src

WORKDIR /src

RUN sed -i "s|$SED_ARG|g" "kg_dial_generator.json"

RUN python -m spacy download en_core_web_sm

CMD gunicorn --workers=1 --timeout 500 --graceful-timeout 500 server:app -b 0.0.0.0:8092
