FROM deeppavlov/base-gpu:0.17.5

RUN pip install git+https://github.com/deepmipt/DeepPavlov.git@a53c42062e4bccf6ec63021ec6bd7b9fbe23f091

WORKDIR /base/DeepPavlov

ARG CONFIG

ARG PORT
ENV CONFIG=$CONFIG
ENV PORT=$PORT

WORKDIR /src
RUN mkdir common

COPY annotators/combined_classification/ ./
COPY common/ common/
RUN ls /tmp

RUN pip install -r requirements.txt
ARG DATA_URL=http://files.deeppavlov.ai/dream_data/distil9in1/9in1.tar.gz
ADD $DATA_URL ~/.deeppavlov/models
RUN cd ~/.deeppavlov/models && tar -xzvf 9in1.tar.gz && cd -

CMD gunicorn --workers=1 --bind 0.0.0.0:8087 --timeout=300 server:app
