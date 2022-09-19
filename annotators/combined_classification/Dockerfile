FROM deeppavlov/base-gpu:0.12.1
RUN pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.12.1

#RUN rm DeepPavlov

#Set up git lfs for your user account: git lfs install
WORKDIR /base
RUN rm -rf DeepPavlov
RUN git clone https://github.com/dimakarp1996/DeepPavlov.git 
WORKDIR /base/DeepPavlov
RUN git checkout pal-bert+ner

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
ARG DATA_URL=http://files.deeppavlov.ai/alexaprize_data/pal_bert_7in1/model.pth.tar
ADD $DATA_URL /tmp
CMD gunicorn --workers=1 --bind 0.0.0.0:8087 --timeout=300 server:app
