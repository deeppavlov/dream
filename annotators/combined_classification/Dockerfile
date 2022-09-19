FROM deeppavlov/base-gpu:0.17.5
RUN pip install git+https://github.com/dimakarp1996/DeepPavlov.git@clean_multitask_ready

WORKDIR /base/DeepPavlov
RUN git checkout clean_multitask_ready

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
ARG DATA_URL=http://files.deeppavlov.ai/dream_data/6in1/model.pth.tar
ADD $DATA_URL /tmp
CMD gunicorn --workers=1 --bind 0.0.0.0:8087 --timeout=300 server:app

